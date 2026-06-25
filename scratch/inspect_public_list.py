import os
from bs4 import BeautifulSoup

def main():
    html_file = "scratch/draft_list_page.html"
    if not os.path.exists(html_file):
        print(f"Error: {html_file} not found.")
        return
        
    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "html.parser")
    
    # Print out lines that might look like diary items
    # Typically they have classes like "diary-title", "title", "date", or are list items (li)
    print("--- Searching for list items (li) ---")
    lis = soup.find_all("li")
    for li in lis:
        text = li.text.strip().replace('\n', ' ')
        if text and len(text) > 5:
            print(f"LI: {text[:100]}")
            
    print("\n--- Searching for divs with title/date related classes ---")
    divs = soup.find_all("div")
    for div in divs:
        class_list = div.get("class", [])
        class_str = " ".join(class_list)
        if any(kw in class_str for kw in ["title", "item", "entry", "list", "diary"]):
            # Only print if it contains text and isn't too huge
            text = div.text.strip().replace('\n', ' ')
            if text and len(text) < 200:
                print(f"DIV [{class_str}]: {text}")

if __name__ == "__main__":
    main()
