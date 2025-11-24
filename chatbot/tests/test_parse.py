from chatbot.nlp.llm_client import parse_shopping_intent

def main():
    test_cases = [
        "Search for men's Jordan 1 in size 10",
        "Recommend comfortable running shoes for wide feet under $120",
        "Show me details for Nike Shox TL for default fit, Hyper Royal/Black/Metallic Silver in color and size 11M",
        "Show me details for Kobe Air Force 1 Low for default fit, and size 11M",
        "Add Nike Air Force 1 for default fit, black/white in color and size 11M to watchlist",
        "Add Nike Air Max 270 for default fit, white/white/black in color and size 11M to watchlist",
        "Show details for Nike Court Vision Low for default fit,  Wheat/Sail in color and size 11M",
        "Find women's Air Max in size 8 under 60$"
    ]
    
    for sample in test_cases:
        print(f"Input: {sample}")
        result = parse_shopping_intent(sample)
        print(f"Output: {result}\n")

if __name__ == "__main__":
    main()