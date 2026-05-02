import asyncio
import os
from playwright.async_api import async_playwright

async def generate_pdf(filename, output_name):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Path to our HTML
        html_path = os.path.abspath(filename)
        url = f"file://{html_path}"

        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="networkidle")

        output_path = os.path.abspath(output_name)

        print(f"Generating PDF at {output_path}...")
        await page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
        )

        await browser.close()
        print(f"Success for {output_name}!")

async def main():
    await generate_pdf("lily_flyer.html", "lily_flyer.pdf")
    await generate_pdf("lily_poster.html", "lily_poster.pdf")

if __name__ == "__main__":
    asyncio.run(main())
