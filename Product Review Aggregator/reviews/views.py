import json
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from bs4 import BeautifulSoup
import requests
from openai import OpenAI
import google.generativeai as genai
from .models import ReviewAnalysis

def scrape_reviews(url):
    """
    Scrape reviews from the product page.
    This is a basic implementation - you might need to customize it based on the e-commerce site.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # This is a basic implementation - you'll need to customize the selectors
        # based on the specific e-commerce site
        reviews = []
        review_elements = soup.find_all('div', {'class': 'review'})  # Adjust selector as needed
        
        for review in review_elements[:50]:  # Limit to 50 reviews for API efficiency
            rating = review.find('span', {'class': 'rating'})  # Adjust selector as needed
            text = review.find('div', {'class': 'text'})  # Adjust selector as needed
            if rating and text:
                reviews.append({
                    'rating': rating.text.strip(),
                    'text': text.text.strip()
                })
        
        return reviews
    except Exception as e:
        return str(e)

def analyze_with_openai(reviews_text):
    """
    Analyze reviews using OpenAI's API
    """
    try:
        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url="https://api.openai.com/v1"
        )
        
        prompt = f"""Analyze these product reviews and provide:
        1. A bullet-point list of main pros
        2. A bullet-point list of main cons
        3. A short overview paragraph
        4. A percentage breakdown of star ratings (5⭐ to 1⭐)

        Reviews:
        {reviews_text}

        Format the response as JSON with these keys:
        pros (list), cons (list), overview (string), and ratings (object with 5,4,3,2,1 as keys and percentages as values)
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful product review analyzer."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        error_message = str(e)
        if "insufficient_quota" in error_message.lower():
            return "OpenAI API quota exceeded. Please check your billing and usage limits at https://platform.openai.com/account/billing"
        elif "model_not_found" in error_message.lower():
            return "The selected AI model is not available. Please try again later."
        else:
            return f"An error occurred: {error_message}"

def analyze_with_gemma(reviews_text):
    """
    Analyze reviews using Google's Gemma model
    """
    try:
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemma-pro')
        
        prompt = f"""Analyze these product reviews and provide:
        1. A bullet-point list of main pros
        2. A bullet-point list of main cons
        3. A short overview paragraph
        4. A percentage breakdown of star ratings (5⭐ to 1⭐)

        Reviews:
        {reviews_text}

        Format the response as JSON with these keys:
        pros (list), cons (list), overview (string), and ratings (object with 5,4,3,2,1 as keys and percentages as values)
        """

        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        error_message = str(e)
        if "quota" in error_message.lower():
            return "Google API quota exceeded. Please check your billing and usage limits."
        else:
            return f"An error occurred: {error_message}"

def analyze_with_openrouter(reviews_text):
    """
    Analyze reviews using OpenRouter API
    """
    try:
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Analyze these product reviews and provide:
        1. A bullet-point list of main pros
        2. A bullet-point list of main cons
        3. A short overview paragraph
        4. A percentage breakdown of star ratings (5⭐ to 1⭐)

        Reviews:
        {reviews_text}

        Format the response as JSON with these keys:
        pros (list), cons (list), overview (string), and ratings (object with 5,4,3,2,1 as keys and percentages as values)
        """

        data = {
            "model": "anthropic/claude-3-opus-20240229",
            "messages": [
                {"role": "system", "content": "You are a helpful product review analyzer."},
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            return json.loads(result['choices'][0]['message']['content'])
        else:
            return f"OpenRouter API error: {response.text}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

def analyze_reviews(reviews):
    """
    Analyze reviews using the configured AI provider
    """
    # Prepare reviews for analysis
    reviews_text = "\n".join([f"Rating: {r['rating']}\nReview: {r['text']}" for r in reviews])
    
    # Choose the AI provider based on settings
    provider = settings.AI_PROVIDER.lower()
    if provider == 'gemma':
        return analyze_with_gemma(reviews_text)
    elif provider == 'openai':
        return analyze_with_openai(reviews_text)
    else:  # default to openrouter
        return analyze_with_openrouter(reviews_text)

def index(request):
    """
    Render the main page
    """
    return render(request, 'reviews/index.html')

def analyze(request):
    """
    Handle the review analysis request
    """
    if request.method == 'POST':
        try:
            url = request.POST.get('url')
            
            # Check if we already have an analysis for this URL
            existing_analysis = ReviewAnalysis.objects.filter(url=url).first()
            if existing_analysis:
                return JsonResponse({
                    'pros': existing_analysis.pros.split('\n'),
                    'cons': existing_analysis.cons.split('\n'),
                    'overview': existing_analysis.overview,
                    'ratings': {
                        '5': existing_analysis.five_star_percentage,
                        '4': existing_analysis.four_star_percentage,
                        '3': existing_analysis.three_star_percentage,
                        '2': existing_analysis.two_star_percentage,
                        '1': existing_analysis.one_star_percentage
                    }
                })
            
            # Scrape and analyze reviews
            reviews = scrape_reviews(url)
            if isinstance(reviews, str):  # Error occurred
                return JsonResponse({'error': reviews}, status=400)
            
            analysis = analyze_reviews(reviews)
            if isinstance(analysis, str):  # Error occurred
                return JsonResponse({'error': analysis}, status=400)
            
            # Save the analysis
            ReviewAnalysis.objects.create(
                url=url,
                pros='\n'.join(analysis['pros']),
                cons='\n'.join(analysis['cons']),
                overview=analysis['overview'],
                five_star_percentage=analysis['ratings']['5'],
                four_star_percentage=analysis['ratings']['4'],
                three_star_percentage=analysis['ratings']['3'],
                two_star_percentage=analysis['ratings']['2'],
                one_star_percentage=analysis['ratings']['1']
            )
            
            return JsonResponse(analysis)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)
