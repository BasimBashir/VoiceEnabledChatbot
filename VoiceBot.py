import speech_recognition as sr
import pyaudio
import pandas as pd
import torch
from transformers import GPT2TokenizerFast, GPT2LMHeadModel, BertTokenizerFast, BertForSequenceClassification, pipeline
import transformers
import pyttsx3
import datetime
import os
from jellyfish import jaro_winkler_similarity
from gtts import gTTS
import csv
import warnings

warnings.filterwarnings("ignore")

print("===>Loading models. Please wait.../")

# checking the availability of cpu or gpu and then assigning to var
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# load the Tokenizer from disk
filename = './model/gpt2-medium-v2'
tokenizer = GPT2TokenizerFast.from_pretrained(filename)

# load the model from disk
Generative_model = GPT2LMHeadModel.from_pretrained(filename).to(device)
Generative_model.eval()

# Bert Domain Classifier model
BertDomainmodel = BertForSequenceClassification.from_pretrained('./DomainSentimentalModel', num_labels=2)  # .to(device)
BertTokenizerDomain = BertTokenizerFast.from_pretrained('bert-base-uncased')

# Bert classifier that checks if asked question belongs to in-domian or out-domain
YesNoClf = pipeline('sentiment-analysis', model=BertDomainmodel, tokenizer=BertTokenizerDomain, return_all_scores=True)

# Bert Classes Classifier model
BertClassmodel = BertForSequenceClassification.from_pretrained('./ClassesSentimentModel', num_labels=4)  # .to(device)
BertTokenizerClass = BertTokenizerFast.from_pretrained('bert-base-uncased')

# Bert classifier that checks if asked question belongs to which class of the data
classClf = pipeline('sentiment-analysis', model=BertClassmodel, tokenizer=BertTokenizerClass, return_all_scores=True)

# text_list = []
general_history = []
property_history = []
health_history = []
auto_history = []

engine = pyttsx3.init('sapi5')
volume = engine.getProperty('volume')  # getting to know current volume level (min=0 and max=1)
voices = engine.getProperty('voices')
rate = engine.getProperty('rate')  # getting details of current speaking rate

engine.setProperty('rate', 150)  # setting up new voice rate
engine.setProperty('volume', 1.0)  # setting up volume level  between 0 and 1
engine.setProperty('voice', voices[2].id)

print("===>Models Loaded Successfully!\n\n")


def text_to_speech(text, filename, lang="en", accent="com"):
    tts = gTTS(text, lang=lang, tld=accent)
    tts.save(filename)


def speak(txt):
    # print("Nova: ", txt)
    # engine.say(txt)
    engine.save_to_file(txt, './static/answer.mp3')
    # engine.runAndWait()


def wishMe():
    hour = int(datetime.datetime.now().hour)
    if 0 <= hour < 12:
        speak("Good morning!")
    elif 12 <= hour < 15:
        speak("Good afternoon!")
    elif 15 <= hour < 19:
        speak("Good evening!")
    elif 19 <= hour < 24:
        speak("Good night!")
    else:
        speak("How may I help you!")

    speak("I am representing the Visibility Bots as. Nova the insurer bot.. Say bye. to exit")


# insert to csv i.e., database
def write_csv(question, answer, _class):
    # Open CSV file in append mode
    # Create a file object for this file
    with open('./static/data/User_faq_database.csv', 'a', newline='', encoding='utf-8') as f_object:
        # Pass the file object and a list
        # of column names to DictWriter()
        # You will get an object of DictWriter

        fieldnames = ['question', 'answer', 'class']  # Define the column names
        writer = csv.DictWriter(f_object, fieldnames=fieldnames)

        # Pass the dictionary as an argument to the Writerow()
        writer.writerow({'question': question, 'answer': answer, 'class': _class})

        # Close the file object
        f_object.close()


def MIC():
    r = sr.Recognizer()
    mic = sr.Microphone()

    print("Listening")
    with mic as source:
        # r.adjust_for_ambient_noise(source, duration=0)
        audio = r.listen(source)
    return audio, r


def TRANSCRIBE(audio, r):
    audio_list = []
    # create an empty list to store untranscribed audio samples
    untranscribed_audio_list = []

    x = f"{audio}"
    last_four_chars = x[-4:]
    try:
        if x == "A6D0":
            print(last_four_chars)
        else:
            # try to transcribe the audio
            print("start Transcribing")
            text = r.recognize_google(audio, language="en-in")
            if text is None:
                # if unable to transcribe, add to the transcribed audio list
                untranscribed_audio_list.append(audio)
            else:
                # if transcribed successfully, add to the audio list
                audio_list.append(audio)
                if "A6D0" in last_four_chars:
                    audio_list[-1].pop()
                    k = 1

    except sr.UnknownValueError:
        print("Could not understand audio")
        # if unable to transcribe, add to the un-transcribed audio list
        untranscribed_audio_list.append(audio)

    # remove un-transcribed audio samples from the audio list
    audio_list = [audio for audio in audio_list if audio not in untranscribed_audio_list]

    # transcribe the remaining audio samples in the audio list
    text_list = []
    for audio in audio_list:
        text = r.recognize_google(audio, language="en-in")
        if text is None:
            print("Could not understand audio")
            text_list[len(text_list)].pop()
            print('cleared')
        else:
            text_list.append(text)

    if text_list:
        print(text_list[-1])
        return str(text_list[-1])
    else:
        return "empty"


# noinspection PyUnboundLocalVariable
def auto_corr(x):
    # read the tokens from the text file into a list
    with open("essential.txt", "r") as file:
        tokens = file.read().splitlines()
    # print the list of tokens
    main_text = x
    e = []
    word_list = main_text.split()
    for v in range(len(word_list)):
        sim = 0
        word = word_list[v]
        for i in range(len(tokens)):
            similarity = jaro_winkler_similarity(word, tokens[i])
            if sim is None:
                sim = similarity
            else:
                if sim > similarity:
                    sim = sim
                elif sim < similarity:
                    sim = similarity
                    ret = tokens[i]
        if sim >= 0.85:
            e.append(ret)
        elif sim < 0.85:
            e.append(word)
    sentence = ' '.join(e)
    return sentence


# Bert's classification function
def bertDomainpredict(user_input, Clf):
    prediction = Clf(user_input)
    return prediction[0][0]['score']


# Bert's classification function
def bertClasspredict(user_input, Clf):
    prediction = Clf(user_input)
    return prediction[0][0]['score'], prediction[0][1]['score'], prediction[0][2]['score'], prediction[0][3]['score']


# GPT2 generation function with memory adpatation
def generate_answer(question, history):
    # Add the new question to the history
    history.append(question)

    # If the history is longer than 2, remove the oldest question
    if len(history) > 4:
        history.pop(0)

    # Concatenate the previous questions and answers with the current question
    prompt = ""
    for i in range(len(history) - 1):
        prompt += f"question: {history[i]}\nanswer: {generate_answer(history[i], [])}\n"
    prompt += f"question: {history[-1]}\nanswer:"
    # print("Prompt:\n", prompt)
    # Generate the answer using GPT-2
    input_ids = tokenizer.encode(prompt, return_tensors='pt')
    input_ids = input_ids.to(device)
    output = Generative_model.generate(input_ids,
                                       max_length=512,
                                       do_sample=True,
                                       pad_token_id=tokenizer.eos_token_id,
                                       eos_token_id=tokenizer.eos_token_id)

    # Decode the generated answer
    response_text = tokenizer.decode(output[0], skip_special_tokens=True)
    answer = response_text.split('answer: ')[-1]

    # Add the generated answer to the history
    history.append(answer)

    # If the history is longer than 2, remove the oldest answer
    if len(history) > 4:
        history.pop(0)

    return answer


# Function that has the logic for prompt responses alongside retrieval and generative models embediment
def get_voice_response(usrText):
    while True:

        if usrText.lower() == "bye":
            return "Bye", "default prompt"

        GREETING_INPUTS = ["hello", "hi", "greetings", "sup", "what's up", "hey", "hiii", "hii", "yo",
                           "assalam o alaikum"]

        SURPRISED_INPUTS = ["wow", "wonderful", "awesome", "fantastic", "brilliant", "superb", "good"]

        ANGRY_INPUTS = ["shit", "getlost", "get lost", "get-lost", "fuck", "fuckoff", "fuck off", "idiot", "bastard"]

        EXCLAMATORY_INPUTS = ["oh", "ohh", "ohhh", "ohhhhh", "oh...", "ohh...", "ohhh...", "ohhhhh...",
                              "oh.", "ohh.", "ohhh.", "ohhhhh.", "oh..", "ohh..", "ohhh..", "ohhhhh..",
                              "oh!", "ohh!", "ohhh!", "ohhhhh!", "ah", "ahh", "ahhh", "ahhhhh", "ah...", "ahh...",
                              "ahhh...", "ahhhhh...",
                              "ah.", "ahh.", "ahhh.", "ahhhhh.", "ah..", "ahh..", "ahhh..", "ahhhhh..",
                              "ah!", "ahh!", "ahhh!", "ahhhhh!", "huh", "huhh", "huhhh", "huh.", "huhh.", "huhhh.",
                              "huh..", "huhh..", "huhhh..", "huh...", "huhh...", "huhhh...", "huh!", "huhh!", "huhhh!",
                              "hm", "hmm", "hmmm", "hmmmm", "hm.", "hmm.", "hmmm.", "hmmmm.",
                              "hm..", "hmm..", "hmmm..", "hmmmm..", "hm...", "hmm...", "hmmm...", "hmmmm...",
                              "hm!", "hmm!", "hmmm!", "hmmmm!"]

        HARD_INPUTS = ["How are you?", "How are you", "How are u?", "How are u", "How are u.", "How are you."]

        YES_INPUTS = ["yes", "yes.", "yes..", "yes...", "yess", "yesss", "yessss", "yess.", "yesss.", "yessss.",
                      "yess..", "yesss..", "yessss..", "yess...", "yesss...", "yessss..."]

        NO_INPUTS = ["no", "no.", "no..", "no...", "noo", "nooo", "noooo", "noo.", "nooo.", "noooo.",
                     "noo..", "nooo..", "noooo..", "noo...", "nooo...", "noooo..."]

        a = [x.lower() for x in GREETING_INPUTS]

        sd = ["Thanks", "Welcome"]

        d = [x.lower() for x in sd]

        am = ["OK"]

        c = [x.lower() for x in am]

        SI = [x.lower() for x in SURPRISED_INPUTS]

        AI = [x.lower() for x in ANGRY_INPUTS]

        EI = [x.lower() for x in EXCLAMATORY_INPUTS]

        HI = [x.lower() for x in HARD_INPUTS]

        YI = [x.lower() for x in YES_INPUTS]

        NI = [x.lower() for x in NO_INPUTS]

        if usrText.lower() in a:
            return "Hi, I'm Nova representing Visiblity Bots!\U0001F60A", "default prompt"

        if usrText.lower() in c:
            return "Ok...Alright!\U0001F64C", "default prompt"

        if usrText.lower() in d:
            return "My pleasure! \U0001F607", "default prompt"

        if usrText.lower() in SI:
            return "JazakaAllah! \U0001F607", "default prompt"

        if usrText.lower() in AI:
            return "I am a Language model. You shouldn't be saying such words. \U0001F620", "default prompt"

        if usrText.lower() in EI:
            return "Yeah! \U0001F44D", "default prompt"

        if usrText.lower() in HI:
            return "I'm fine. How can i help you with insurance?", "default prompt"

        if usrText.lower() in YI:
            return "ok...", "default prompt"

        if usrText.lower() in NI:
            return "oh...", "default prompt"

        else:
            if bertDomainpredict(usrText, YesNoClf) >= 0.27:  # set this threshold to get better classification

                GENERAL, PROPERTY, HEALTH, AUTO = bertClasspredict(usrText, classClf)  # Class predictor classifier

                if HEALTH > PROPERTY and HEALTH > AUTO and HEALTH > GENERAL and HEALTH > 0.30:  # for health insurance
                    a = generate_answer(usrText, health_history)
                    print("<---Health Insurance--->")
                    find_CLASS = "Health Insurance"
                elif PROPERTY > HEALTH and PROPERTY > AUTO and PROPERTY > GENERAL and PROPERTY > 0.30:  # for property insurance
                    a = generate_answer(usrText, property_history)
                    print("<---Property Insurance--->")
                    find_CLASS = "Property Insurance"
                elif AUTO > PROPERTY and AUTO > HEALTH and AUTO > GENERAL and AUTO > 0.50:  # for Auto insurance
                    a = generate_answer(usrText, auto_history)
                    print("<---Auto Insurance--->")
                    find_CLASS = "Auto Insurance"
                else:  # if None is greater then general insurance
                    a = generate_answer(usrText, general_history)
                    print("<---General Insurance--->")
                    find_CLASS = "General Insurance"

                if len(a) > 1:
                    return a, find_CLASS
                else:
                    return "I didn't understand your question. What was it precisely? ", "default prompt"
            else:
                return "I am sorry i am Language model, Ask me anything regarding Insurance or write Question in more generic way!", "default prompt"


# Function to IO chat in voice
def voiceCommand(user_input):
    mic_input, access = MIC()
    user_input = TRANSCRIBE(mic_input, access)
    question = auto_corr(user_input)
    if question == "empty":
        pass
    else:
        answer = get_voice_response(question)
        return speak(answer)


# if __name__ == "__main__":
#     wishMe()
#
#     while True:
#         mic_input, access = MIC()
#         user_input = TRANSCRIBE(mic_input, access)
#         question = auto_corr(user_input)
#         if question == "bye":
#             break
#         if question == "empty":
#             pass
#         else:
#             reply, _class = get_voice_response(question)
#             speak(reply)
#         write_csv(user_input, reply, _class)
