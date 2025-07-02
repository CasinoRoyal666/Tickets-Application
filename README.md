# TicketsApp

--HOW TO RUN PROJECT--
First of all, get all dependencies from "requirements.txt" file. You need to:
- Open Terminal
- Go to root directory of the project (Tickets-Application)
- Create a virtual enviroment : "python -m venv venv"
- Activate virtual enviroment : ".\venv\Scripts\activate"
- Install all dependencies : "pip install -r requirements.txt"

Next, you can see ".env.example" file. Create ".env" file in the root directory, copy the lines from ".env.exaple" and replace the examples in it with your real data of the created database in PostgreSQL. 
To get SECRET_KEY field, you need to:

- Activate virtual enviroment : ".\venv\Scripts\activate"
- Write "python". This will create a Python shell
- Write these commands : "from django.core.management.utils import get_random_secret_key" smash ENTER "print(get_random_secret_key())"
- You got a SECRET_KEY! Copy and paste in the SECRET_KEY field

--TESTS--

To run tests, write "pytest" in terminal. Also, you can run command "pytest" from different directories, not only in the root folder of the project (Ticket-Application);

To run specific file, for example "test_event_serializer.py" use "pytest events/tests/event/test_event_serializers.py" command;

To run specific test, for example "test_create_order_with_items" from "test_order_serializers.py" use "pytest events/tests/order/test_order_serializers.py::test_create_order_with_items" command in root directory, or just 
"pytest test_order_serializers.py::test_create_order_with_items" from test file directory.

--API TESTS--
To run API tests use Postman (or something else). In URL field write "http://127.0.0.1:8000/events/" or   "http://127.0.0.1:8000/orders/"

Some examples for tests:
- Post new order:    Choose POST and URL "http://127.0.0.1:8000/orders/", also in HEADERS choose "Content-Type"  - "application/json"
- In "BODY":     {
    "customer_name": "Postman",
    "customer_email": "postpost@gmail.com",
    "customer_phone": "375257661875",
    
    "items": [
        {
            "event": 1,
            "quantity": 2
        }
    ]
}
- You see the status "201 CREATED" and info about a new order.
