from dash import Dash, html, dcc, callback, Output, Input, State
import plotly.express as px
import pandas as pd
import requests
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import time

app = Dash(__name__)



def generate_image_from_prompt(prompt):  
    try:
        # Get Azure OpenAI Service settings
        load_dotenv()
        api_base = os.getenv("AZURE_OAI_ENDPOINT")
        api_key = os.getenv("AZURE_OAI_KEY")
        api_version = '2023-06-01-preview'

        # Make the initial call to start the job
        url = "{}openai/images/generations:submit?api-version={}".format(api_base, api_version)
        headers= { "api-key": api_key, "Content-Type": "application/json" }
        body = {
            "prompt": prompt,
            "n": 2,
            "size": "512x512"
        }
        submission = requests.post(url, headers=headers, json=body)

        # Get the operation-location URL for the callback
        operation_location = submission.headers['Operation-Location']

        # Poll the callback URL until the job has succeeeded
        status = ""
        while (status != "succeeded"):
            time.sleep(3) # wait 3 seconds to avoid rate limit
            response = requests.get(operation_location, headers=headers)
            status = response.json()['status']

        print(response.json())
        # Get the results
        image_url = response.json()['result']['data'][0]['url']

        # Return the URL for the generated image
        return image_url

    except Exception as ex:
        print(ex)


def generate_prompt(value):
    load_dotenv()
    azure_oai_endpoint = os.getenv("AZURE_OAI_ENDPOINT")
    azure_oai_key = os.getenv("AZURE_OAI_KEY")
    azure_oai_model = os.getenv("AZURE_OAI_MODEL")

    client = AzureOpenAI(
        azure_endpoint = azure_oai_endpoint, 
        api_key=azure_oai_key,  
        api_version="2023-05-15"
    )

    response = client.chat.completions.create(
        model=azure_oai_model,
        temperature=0.7,
        max_tokens=120,
        messages=[
            {"role": "system", "content": "You are an expert at generating DallE prompts"},
            {"role": "user", "content": value}
        ]
    )

    print(response.choices[0].message.content)


    prompt = response.choices[0].message.content

    image_url = generate_image_from_prompt(prompt)

    return image_url


app.layout = html.Div([
    html.H1(children="Lekan's Image Generation App", style={'textAlign':'center'}),
    dcc.Input(
        id="basic-prompt-input",
        type="text",
        placeholder="type your basic prompt here",
        size="100",
    ),
    html.Button('Submit', id='submit-button', n_clicks=0),
    html.Div(id='image-generation-output',
             children=''),
    html.Img(id="generated-image")
])


@callback(
    Output('generated-image', 'src'),
    Input('submit-button', 'n_clicks'),
    State('basic-prompt-input', 'value'),
    prevent_initial_call=True
)
def generate_image(n_clicks, value):
    image_url = generate_prompt(value)

    return image_url

if __name__ == '__main__':
    app.run(debug=True)
