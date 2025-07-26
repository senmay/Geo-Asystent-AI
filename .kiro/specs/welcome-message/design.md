# Design Document

## Overview

Funkcjonalność wiadomości powitalnej zostanie zaimplementowana poprzez automatyczne dodanie wiadomości od bota do stanu czatu przy pierwszym załadowaniu komponentu Chat. Rozwiązanie wykorzystuje istniejącą infrastrukturę wiadomości i nie wymaga zmian w API backend.

## Architecture

### Frontend-Only Solution
- Wiadomość powitalna będzie generowana po stronie frontend
- Wykorzystamy istniejący system wiadomości (Message interface)
- Implementacja w hooku useChat z użyciem useEffect
- Brak potrzeby zmian w backend API

### Component Flow
```
App.tsx → Chat.tsx → useChat hook → inicjalizacja z welcome message
```

## Components and Interfaces

### Modified Components

#### 1. useChat Hook (`frontend/src/hooks/useChat.ts`)
- **Nowa funkcjonalność**: `initializeWelcomeMessage()`
- **Modyfikacja**: Dodanie useEffect do automatycznej inicjalizacji
- **Stan**: Dodanie flagi `isInitialized` do śledzenia czy wiadomość została już wyświetlona

#### 2. Message Interface (istniejący)
```typescript
interface Message {
  sender: 'user' | 'bot';
  text: string;
  type?: 'info' | 'data';
}
```
- Wykorzystamy typ 'info' dla wiadomości powitalnej

### Welcome Message Content
Wiadomość będzie zawierać:
- Przedstawienie asystenta jako "Geo-Asystent AI"
- Krótki opis możliwości systemu
- 2-3 przykłady zapytań w języku polskim
- Przyjazny, profesjonalny ton

### Example Welcome Message
```
Cześć! Jestem Geo-Asystent AI - Twój asystent do pracy z danymi przestrzennymi.

Mogę pomóc Ci w:
• Wyszukiwaniu i analizie działek
• Znajdowaniu budynków i ich właściwości  
• Lokalizacji stacji GPZ i infrastruktury
• Wykonywaniu operacji przestrzennych (bufory, przecięcia)

Przykłady zapytań:
- "pokaż największą działkę"
- "znajdź budynki w pobliżu GPZ"
- "ile działek jest w bazie danych?"

Zadaj mi pytanie o dane GIS!
```

## Data Models

### Welcome Message State
```typescript
interface WelcomeState {
  isInitialized: boolean;
  welcomeMessage: Message;
}
```

### Session Management
- Wykorzystanie stanu komponentu (nie localStorage)
- Wiadomość pojawi się przy każdym nowym załadowaniu aplikacji
- Brak persistencji między sesjami (zgodnie z wymaganiami)

## Error Handling

### Edge Cases
1. **Błąd podczas inicjalizacji**: Graceful fallback - aplikacja działa normalnie bez wiadomości powitalnej
2. **Wielokrotne inicjalizacje**: Flaga `isInitialized` zapobiega duplikowaniu wiadomości
3. **Błąd renderowania**: Istniejący system obsługi błędów w ChatHistory

### Error Recovery
- Brak krytycznych błędów - funkcjonalność jest dodatkiem
- W przypadku problemów aplikacja działa normalnie
- Logowanie błędów do konsoli dla debugowania

## Testing Strategy

### Unit Tests
1. **useChat Hook Tests**
   - Test inicjalizacji wiadomości powitalnej
   - Test że wiadomość pojawia się tylko raz
   - Test że normalne funkcjonalności czatu działają po inicjalizacji

2. **Integration Tests**
   - Test renderowania wiadomości powitalnej w ChatHistory
   - Test że wiadomość ma odpowiedni typ i format
   - Test interakcji z istniejącymi wiadomościami

### Test Scenarios
```typescript
describe('Welcome Message', () => {
  it('should display welcome message on first load')
  it('should not duplicate welcome message on re-renders')
  it('should allow normal chat after welcome message')
  it('should handle welcome message initialization errors gracefully')
})
```

### Manual Testing
1. Odświeżenie strony - wiadomość powinna się pojawić
2. Wysłanie normalnej wiadomości - chat powinien działać normalnie
3. Sprawdzenie formatowania i stylu wiadomości
4. Test w różnych przeglądarkach

## Implementation Approach

### Phase 1: Core Implementation
1. Modyfikacja useChat hook - dodanie inicjalizacji
2. Stworzenie funkcji generateWelcomeMessage()
3. Dodanie useEffect do automatycznego wywoływania

### Phase 2: Content and Styling
1. Sfinalizowanie treści wiadomości powitalnej
2. Upewnienie się że styling jest spójny z istniejącymi wiadomościami
3. Test różnych długości tekstu

### Phase 3: Testing and Polish
1. Napisanie testów jednostkowych
2. Testy manualne w różnych scenariuszach
3. Optymalizacja wydajności jeśli potrzebna

## Technical Considerations

### Performance
- Minimalne obciążenie - tylko jedna dodatkowa wiadomość w stanie
- Brak dodatkowych API calls
- Wykorzystanie istniejącej infrastruktury renderowania

### Maintainability
- Czysta separacja logiki welcome message
- Łatwa modyfikacja treści wiadomości
- Brak wpływu na istniejące funkcjonalności

### Scalability
- Rozwiązanie może być łatwo rozszerzone o więcej typów wiadomości systemowych
- Możliwość dodania konfiguracji wiadomości powitalnej
- Potencjał do personalizacji w przyszłości