import os
import requests # for making HTTP requests
from bs4 import BeautifulSoup # for parsing HTML
import json
import smtplib # for sending emails
from email.message import EmailMessage # for creating email messages


# --- Configuration ---
# It's highly recommended to set these as environment variables for security.
# You can get a free Serper API key from https://serper.dev
SERPER_API_KEY = "479299cdec734440be8b457d83617b16a3feedeb"


# Ollama Configs
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b") # Assumes you have pulled a gemma3 model

# SMTP Configuration for the email tool
SMTP_SERVER = os.environ.get("SMTP_SERVER")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 465)) # Default to 465 for SSL
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")


# search the web for the query
# return a formatted string of search results
# if the search is not successful, return an error message
def search_web(query:str) -> str:
    if not SERPER_API_KEY:
        print("--- DEBUG: SERPER_API_KEY is not set. ---")
        return "Error: SERPER_API_KEY is not set. Cannot perform web search."
    print(f"--- DEBUG: Using SERPER_API_KEY ending in '...{SERPER_API_KEY[-4:]}' ---")

    payload = json.dumps({"q": query}) # convert the query to a json string
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    try:
        response = requests.post("https://google.serper.dev/search", headers=headers, data=payload)
        print(f"--- DEBUG: Serper API response status code: {response.status_code} ---") # print the status code of the response
        print(f"--- DEBUG: Serper API response text: {response.text[:500]} ... ---") # print the first 500 characters of the response text
        response.raise_for_status() # Raise an exception for bad status codes
        results = response.json() # parse the response as a json object

        if not results.get("organic"): # If no good search results are found, return an error message
            return "No good search results found."

        output = "Search Results:\n"
        for item in results["organic"][:5]: # Get top 5 results
            output += f"- Title: {item.get('title', 'N/A')}\n"
            output += f"  Link: {item.get('link', 'N/A')}\n"
            output += f"  Snippet: {item.get('snippet', 'N/A')}\n\n"

        return output
    except requests.exceptions.RequestException as e:
        return f"Error during web search: {e}"

# browse a website and return the text content
# if the browsing is not successful, return an error message
# return the first 8000 characters of the text to avoid overwhelming the model
def browse_website(url:str) -> str:
    """
    Scrapes the text content of a given URL.
    Returns the cleaned text content or an error message if it fails.
    """
    print(f"-- tool: Attempting to browse website '{url}' --")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1'
        }
        response = requests.get(url, headers=headers, timeout=15) # make the request to the website
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser') # parse the response content as HTML

        # remove the script and style tags from the HTML to avoid parsing errors
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose() # remove the script and style tags

        text = soup.get_text() # get the text content of the HTML
        lines = (line.strip() for line in text.splitlines()) # split the text into lines and strip whitespace
        chunks = (phrase.strip() for line in lines for phrase in line.split("  ")) # split the lines into phrases and strip whitespace
        text = '\n'.join(chunk for chunk in chunks if chunk) # join the phrases into a single string

        if not text: # if the text is empty, return an error message
            return f"Error: No text content found at {url}"

        print(f"-- tool: Successfully browsed {url} --")
        return text[:8000] # return the first 8000 characters of the text to avoid overwhelming the model

    except requests.exceptions.RequestException as e:
        return f"Error browsing website {url}: {e}"


def send_email(to_address: str, subject: str, body: str) -> str:
    """
    Sends an email using the configured SMTP settings.
    """
    print(f"--- Tool: Sending email to '{to_address}' ---")
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD]):
        return "Error: SMTP settings are not fully configured. Cannot send email."

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USERNAME
    msg['To'] = to_address

    try:
        # Use SMTP_SSL for port 465
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        return f"Email sent successfully to {to_address}."
    except Exception as e:
        return f"Error sending email: {e}"




def call_gemma_ollama(prompt:str, output_format:str = "json") -> str:
    """
    Calls the Gemma Ollama model with the given prompt and output format.
    Returns the response from the model or an error message if it fails.
    """

    print(f"--- Tool [call_gemma_ollama]: calling gemme ollama model API and get the response ---")
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    if output_format == "json":
        payload["format"] = "json" # set the output format to json
    try:
        # print(f"--- Tool [call_gemma_ollama]: payload: {payload} ---")
        response = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=60) # make the request to the ollama API
        response.raise_for_status() # raise an exception for bad status codes
        result = response.json() # parse the response as a json object
        return result.get("response", "{}") # return the response from the model

    except requests.exceptions.Timeout:
        return "Error: Ollama API request timed out. The model might be taking too long to respond."
    except requests.exceptions.RequestException as e:
        return f"Error calling Gemma Ollama: {e}. Is Ollama running?"
    except (KeyError, IndexError) as e:
        return f"Error parsing Gemma Ollama response: {e}. Response: {response.text}"
    except Exception as e:
        return f"Error calling Gemma Ollama: {e}"






def run_concierge_agent(goal: str, history: list) -> str:
    """
    Runs the main logic of the concierge agent, now with conversation history and robust multi-site browsing.
    Returns the final summary to be added to the history.
    """

    # 0. Extract Email address from the goal if it exits
    prompt_extract_email = f"""
    You are an expert at finding email addresses in text.
    Analyze the following user request and extract the email address if one is present.
    If you find an email address, respond with ONLY the email address.
    If you do not find an email address, respond with the word "none".

    User request: "{goal}"
    """
    recipient_email_from_goal = call_gemma_ollama(prompt_extract_email, output_format="text").strip()

    if "@" not in recipient_email_from_goal:
        recipient_email_from_goal = "none"

    print(f"--- Tool: Extracted email address: {recipient_email_from_goal} ---")

    print(f"\n🎯 Goal: {goal}\n")

    formatted_history = "\n".join(history)

    # 1. Decide what to search for
    prompt1 = f"""
You are a helpful concierge agent. Your task is to understand a user's request and generate a concise, effective search query to find the information they need.

Conversation history:
---
{formatted_history}
---
User's latest request: "{goal}"

Based on the request, what is the best, simple search query for Google?
The query should be 3-5 words.
Respond with ONLY the search query itself.
"""
    send_query = call_gemma_ollama(prompt1, output_format="text").strip()
    print(f"--- Tool: Search query: {send_query} ---")

    # 2. search the web
    search_results = search_web(send_query)
    print(f"--- Tool: Search results:\n\n {search_results} \n\n ---")


    # 4. choose which sites to browse
    prompt2 = f"""
You are a smart web navigator. Your task is to analyze Google search results and select the most promising URLs to find the answer to a user's goal. Avoid generic homepages (like yelp.com or google.com) and prefer specific articles, lists, or maps.

User's goal: "{goal}"

Search Results:
---
{search_results}
---

Based on the user's goal and the search results, which are the top 2-3 most promising and specific URLs to browse for details?
Respond with ONLY a list of URLs, one per line.
"""
    browse_urls_str = call_gemma_ollama(prompt2, output_format="text").strip()
    browse_urls = [url.strip() for url in browse_urls_str.split('\n') if url.strip().startswith('http')]
    if not browse_urls:
        print("--- Could not identify promising URLs to browse. Trying to summarize from search results directly. ---")
        # If no URLs are chosen, try to summarize from the snippets
        prompt_summarize_snippets = f"""
        You are a helpful concierge agent. The web browser is not working, but you have search result snippets.
        User's goal: "{goal}"
        Search Results:
        ---
        {search_results}
        ---
        Please provide a summary based *only* on the search result snippets. Do not suggest browsing URLs.
        """
        final_summary = call_gemma_ollama(prompt_summarize_snippets, output_format="text")
        print("\n--- Here is your summary ---\n")
        print(final_summary)
        print("\n--------------------------\n")
        return final_summary
    else:
        print(f"--- Tool: Identified {len(browse_urls)} promising URLs to browse ---")

    # 4. browse the websites and collect information
    all_website_texts = []
    for url in browse_urls:
        text = browse_website(url) # browse the website and get the text content
        if not text.startswith("Error"):
            all_website_texts.append(f"Content from {url}:\n{text}") # add the text content to the list
        else:
            print(f"--- Skipping {url} due to an error. ---")

    if not all_website_texts: # if no text content is found, return an error message
        return "I tried to browse several websites but was blocked or couldn't find any information. Please try again."

    aggregated_text = "\n\n---\n\n".join(all_website_texts)


        # 5. Summarize everything for the user
    prompt3 = f"""
You are a meticulous and trustworthy concierge agent. Your primary goal is to provide a clear, concise, and, above all, ACCURATE answer to the user's request by synthesizing information from multiple sources.

User's latest request: "{goal}"

You have gathered the following text from one or more websites:
---
{aggregated_text}
---

Fact-Check and Synthesize:
Based on the information above, provide a comprehensive summary that directly answers the user's request.
Before including any business or item in your summary, you MUST verify that it meets ALL the specific criteria from the user's request (e.g., hours of operation, location, specific features).
If you cannot find explicit confirmation that a business meets a criterion, DO NOT include it in the summary. It is better to provide fewer, accurate results than more, inaccurate ones.

Format your response clearly for the user. If listing places, use bullet points.
"""
    final_summary = call_gemma_ollama(prompt3, output_format="text")

    print("\n--- Here is your summary ---\n")
    print(final_summary)
    print("\n--------------------------\n")

    # 6. decide if an email should be sent and generate its content




def main():
    """
    The main function that runs the terminal application loop.
    """
    if not SERPER_API_KEY:
        print("🔴 FATAL ERROR: SERPER_API_KEY environment variable not set.")
        print("Please get a free key from https://serper.dev and set the variable.")
        return

    print(f"🤖 Hello! I am your Local Concierge Agent, powered by a local {OLLAMA_MODEL} model.")
    print("   I can remember our conversation and browse multiple sites for you.")
    print("   If you configure your SMTP settings, I can also send emails.")
    print("   Make sure Ollama is running in the background.")
    print('   Type "quit" or "exit" to end the session.')

    conversation_history = []
    user_goal = "I want to find a asia food restaurant in Munich. Send outcome  to mytestemail@gmail.com"
    agent_summary = run_concierge_agent(user_goal, conversation_history)
    conversation_history.append(f"User: {user_goal}")
    conversation_history.append(f"Agent: {agent_summary}")
    print(f"--- Final Summary: {agent_summary} ---")
    print(f"--- Conversation History: {conversation_history} ---")


if __name__ == "__main__":
    main()
