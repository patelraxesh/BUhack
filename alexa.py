from flask import Flask, request
from flask_ask import Ask, statement, question, session
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from firebase import firebase
import requests
import json
import time
import random

ACCOUNT_SID = "AC2bfb2dfdd42e75f169ca972319bec121"
AUTH_TOKEN = "e511f9c1afaa564be32425e900a3265b"
TWILIO_NUMBER = "+16178906207"

client = Client(ACCOUNT_SID, AUTH_TOKEN)

app = Flask(__name__)
ask = Ask(app, "/")

questions_replied = dict()
question_no = 0
question_str = ""

firebase = firebase.FirebaseApplication('https://dietpro-firebase.firebaseio.com', None)
#result = firebase.get('/users', None)

restrict_food = {
	"Flu":["Caffeine","Milk","Cream","Butter","Alcohol","Cigars","Cigarettes","Ice Cream","Cheese","Yogurt","Sour Cream","Mozzarella","Cheddar","Cheese Pizza"],
	"Acid Reflux":["Alcohol","Caffeine","Chocolate","Coke","Pepsi","Canned Food","Tomatoes","Mints","Garlic"]
}
recommended_food = {
	"Flu":["Apple","Oranges","Chicken Soup","Garlic","Banana","Oatmeal","Strawberries", "Cranberries", "Blueberries", "Blackberries","Avocado","Spinach","Salmon"],
	"Acid Reflux":["Bread","Rice","Oatmeal","Melon","Pear","Banana","Ginger","Chamomile Tea"]
}
medicine = {
	"Acetaminophen":"Flu",
	"Ibuprofen":"Flu",
	"Tylenol":"Flu",
	"Advil":"Flu",
	"Nyquil":"Flu",
	"Dayquil":"Flu",
	"Zantac":"Acidity",
	"Prilosec":"Acidity"
}

userdata = {"medicine":["Ibuprofen"],"disease": "Flu"}

@app.route("/sms", methods=['POST'])
def hello():
	in_text = request.form["Body"]
	ph_number = request.form["From"]
	in_text = in_text.lower()
	out_text = get_response(in_text, ph_number)
	response = MessagingResponse()
	response.message(out_text)
	return str(response)

@app.route("/userdata",methods=['POST'])
def get_user_data():
	data = request.get_json()
	userdata["medicine"] = data["medicine"][0]
	userdata["disease"] = medicine[userdata["medicine"]]
	if "medicine" in data.keys():
		return "Success"
	else:
		return "Failure"


@app.route('/call', methods=['POST'])
def call():
    # Make an outbound call to the provided number from your Twilio number
    call = client.calls.create(to='+18574520056', from_=TWILIO_NUMBER,
                               url="http://demo.twilio.com/docs/voice.xml")

    # Return a message indicating the call is coming
    return 'Call coming in!'

def get_response(input_str, ph_number):
	'''
    Get the response output from input
    '''
	input_str = input_str.lower()
	input_words = input_str.split()

    # question types
	question_type_1 = ['i','eat','today']
	question_type_2 = ['i', "drink"]
	question_type_3 = ['call', 'dietitian']
	question_type_4 = ['can', 'feeling']

	DISEASE = userdata["disease"]
	MEDICINE = userdata["medicine"]

	if all(x in input_str for x in question_type_1):
		try:
			choices = random.sample(recommended_food[DISEASE], 3)
			output_txt = 'Dietpro would reccomend %s, %s, or %s'%(choices[0],choices[1],choices[2])
			return output_txt
		except:
			output_txt = 'Sorry, i did not get that. Please ask your question again.'
			return output_txt
	elif all(x in input_str for x in question_type_2):
		if any(x in input_str for x in restrict_food):
			choices = random.sample(recommended_food[DISEASE], 2)
			output_txt = 'Based on your dietry restrictions, Dietpro would not recommend you to eat that. Here are some options. %s and %s.'%(choices[0],choices[1])
		else:
			output_txt = 'Sure! Enjoy your food'
		return output_txt
	elif all(x in input_str for x in question_type_3):
		output_txt = "You will receive a call from your Dietitian shortly!"
		new_msg = call()
		return output_txt
	elif "hi" in input_str or "Hi" in input_str:
		return "Hi, How can i help you today?"
	elif 'help' in input_str:
		return "\
		Here are some things you can try:\
		\n1) What should i eat today ?\
		\n2) Should i eat pizza today ?\
		\n3) I am feel acidity today, should i eat cookies ?\
		\n4) Whats in my diet plan for today ?\
		\n5) what are my dietary restrictions ?\
		\n6) call my dietitian"
	else:
		return "\
		Here are some things you can try:\
		\n1) What should i eat today ?\
		\n2) Should i eat pizza today ?\
		\n3) I am feel acidity today, should i eat cookies ?\
		\n4) Whats in my diet plan for today ?\
		\n5) what are my dietary restrictions ?\
		\n6) call my dietitian"

@ask.launch
def start_skill():
    output_txt = "Hello, Welcome to DietPRO. You could ask me questions about your diet."
    return question(output_txt)

@ask.intent("eat_specific_food")
def eat_specific_food(food):
	DISEASE = userdata["disease"]
	time.sleep(1)
	try:
		if food.title() in restrict_food[DISEASE]:
			choices = random.sample(recommended_food[DISEASE], 2)
			output_txt = 'Based on your dietry restrictions, Dietpro would not recommend you %s. Here are some options. %s and %s.'%(food,choices[0],choices[1])
		else:
			output_txt = 'Sure! Enjoy your %s'%(food)
			return statement(output_txt)
	except:
		output_txt = 'Sorry, i did not get that. Please ask your question again.'
		return question(output_txt)

@ask.intent("eat_today")
def eat_today():
	DISEASE = userdata["disease"]
	time.sleep(1)
	try:
		choices = random.sample(recommended_food[DISEASE], 3)
		output_txt = 'Dietpro would reccomend %s, %s, or %s'%(choices[0],choices[1],choices[2])
		return statement(output_txt)
	except:
		output_txt = 'Sorry, i did not get that. Please ask your question again.'
		return question(output_txt)

@ask.intent("other_problem")
def other_problem(problem,food):
	DISEASE = userdata["disease"]
	MEDICINE = userdata["medicine"]
	time.sleep(1)
	try:
		print problem, food, restrict_food[DISEASE], restrict_food[problem]
		if food.title() in restrict_food[DISEASE] or food.title() in restrict_food[problem.title()]:
			output_txt = 'You are taking %s and you feel %s. Dietpro will not recommend eating %s'%(MEDICINE, problem, food)
		else:
			output_txt = 'Sure! Enjoy your %s'%(food)
		return statement(output_txt)
	except:
		output_txt = 'Sorry, i did not get that. Please ask your question again.'
		return question(output_txt)

if __name__ == '__main__':
    app.run(debug=True)
