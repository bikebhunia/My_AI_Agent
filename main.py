import asyncio
from playwright.async_api import async_playwright
from google import genai
import config

# Initialize Gemini client with your API key
client = genai.Client(api_key=config.API_KEY)


async def scrape_reviews(url):
    reviews = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--window-size=800,3200"]
        )
        page = await browser.new_page()
        await page.set_viewport_size({"width": 800, "height": 3200})
        await page.goto(url)
        await page.wait_for_selector(".jftiEf")

        elements = await page.query_selector_all(".jftiEf")
        for element in elements:
            try:
                # Click "More" button if present
                more_btn = await element.query_selector(".w8nwRe")
                if more_btn:
                    await more_btn.click()
                    await page.wait_for_timeout(5000)
            except Exception:
                pass

            # Extract review text
            snippet = await element.query_selector(".MyEned")
            if snippet:
                text = await snippet.text_content()
                reviews.append(text.strip())

        await browser.close()

    return reviews


def summarize(reviews):
    prompt = (
        "I collected some reviews of a place I was considering visiting. "
        "Can you summarize the reviews for me? I want to generally know what people "
        "like and dislike. The reviews are below:\n"
    )
    for review in reviews:
        prompt += "\n" + review

    # Use Gemini to generate the summary
    response = client.models.generate_content(
        model="gemini-2.0-flash",  # You can change the model as needed
        contents=prompt,
        config={
            "temperature": 0,
            "max_output_tokens": 300,
        },
    )

    return response.text


# Main execution
url = input("Enter a URL: ")
reviews = asyncio.get_event_loop().run_until_complete(scrape_reviews(url))
result = summarize(reviews)
print(result)

