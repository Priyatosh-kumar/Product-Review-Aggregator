# Product Review Aggregator

A Django web application that analyzes product reviews from e-commerce websites using OpenAI's ChatGPT API.

## Features

- Paste any e-commerce product URL
- Automatic review scraping
- AI-powered review analysis
- Concise summary with pros and cons
- Star rating breakdown

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Deployment

This application is configured for deployment on Vercel. The `vercel.json` file contains the necessary configuration.

## Technologies Used

- Django
- OpenAI API
- BeautifulSoup4
- Requests
- Vercel 