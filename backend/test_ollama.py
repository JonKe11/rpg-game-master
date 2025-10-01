# backend/test_ollama.py
import ollama

try:
    client = ollama.Client()
    
    # Sprawdź dostępne modele
    print("Dostępne modele:")
    models = client.list()
    
    # Wypisz strukturę aby zobaczyć co zwraca
    if 'models' in models:
        for model in models['models']:
            # Użyj .get() aby uniknąć KeyError
            name = model.get('name', 'Unknown')
            size = model.get('size', 'Unknown')
            print(f"- {name} (size: {size})")
    else:
        print("Struktura:", models)
    
    # Test generowania z twoim modelem
    print("\n\nTest generowania z llama3.1:8b...")
    response = client.generate(
        model='llama3.1:8b',  
        prompt='Opisz krótko kantynę w Star Wars po polsku'
    )
    print("Odpowiedź:")
    print(response['response'])
    
except Exception as e:
    print(f"Błąd: {e}")
    print("\nSprawdź czy Ollama jest uruchomiona:")
    print("ollama serve")