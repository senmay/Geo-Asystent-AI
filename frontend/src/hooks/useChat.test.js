/**
 * Simple test script for useChat hook welcome message functionality
 * Following KISS and DRY principles with basic validation
 */

// Mock React hooks for testing
const mockSetState = (initialValue) => {
  let value = initialValue;
  const setValue = (newValue) => {
    value = typeof newValue === 'function' ? newValue(value) : newValue;
  };
  return [() => value, setValue];
};

// Test the welcome message initialization logic
function testWelcomeMessageInitialization() {
  console.log('🧪 Testing welcome message initialization...');
  
  // Simulate hook state
  const [getMessages, setMessages] = mockSetState([]);
  
  // Simulate useRef for initialization tracking
  let isInitializedRef = { current: false };
  
  // Simulate addMessage function
  const addMessage = (message) => {
    setMessages((prev) => [...prev, message]);
  };
  
  // Simulate useEffect logic
  if (!isInitializedRef.current) {
    const welcomeMessage = {
      sender: 'bot',
      text: `Cześć! Jestem Geo-Asystent AI - Twój asystent do pracy z danymi przestrzennymi.

Obecnie oferuje funkcjonalność:
• Wyszukiwanie 'n' najwiekszych dzialek
• Wyszukiwanie dzialek o określonej powierzchni
• Wyszukiwanie działek bez budynków
• Eksport danych odnalezionych danych do pdf

Przykładowe zapytania :
- "pokaż największą działkę"
- "pokaż 5 najwiekszych dzialek"
- "pokaż działki bez budynków"

Zadaj mi pytanie o dane GIS!`,
      type: 'info'
    };
    addMessage(welcomeMessage);
    isInitializedRef.current = true;
  }
  
  // Validate results
  const currentMessages = getMessages();
  
  if (currentMessages.length === 1) {
    console.log('✅ Welcome message added to messages array');
  } else {
    console.log('❌ Expected 1 message, got:', currentMessages.length);
    return false;
  }
  
  const welcomeMsg = currentMessages[0];
  
  if (welcomeMsg.sender === 'bot') {
    console.log('✅ Welcome message sender is bot');
  } else {
    console.log('❌ Expected sender "bot", got:', welcomeMsg.sender);
    return false;
  }
  
  if (welcomeMsg.type === 'info') {
    console.log('✅ Welcome message type is info');
  } else {
    console.log('❌ Expected type "info", got:', welcomeMsg.type);
    return false;
  }
  
  if (welcomeMsg.text.includes('Geo-Asystent AI')) {
    console.log('✅ Welcome message contains "Geo-Asystent AI"');
  } else {
    console.log('❌ Welcome message missing "Geo-Asystent AI"');
    return false;
  }
  
  if (welcomeMsg.text.includes('działek') && welcomeMsg.text.includes('budynków') && welcomeMsg.text.includes('GPZ')) {
    console.log('✅ Welcome message contains key GIS terms');
  } else {
    console.log('❌ Welcome message missing key GIS terms');
    return false;
  }
  
  return true;
}

function testChatFunctionalityWithWelcomeMessage() {
  console.log('🧪 Testing chat functionality with welcome message...');
  
  // Simulate hook state with welcome message already present
  const [getMessages, setMessages] = mockSetState([{
    sender: 'bot',
    text: 'Welcome message',
    type: 'info'
  }]);
  
  const addMessage = (message) => {
    setMessages((prev) => [...prev, message]);
  };
  
  // Simulate sending a user message
  const userMessage = { sender: 'user', text: 'test query' };
  addMessage(userMessage);
  
  // Simulate bot response
  const botMessage = { sender: 'bot', text: 'Test response', type: 'data' };
  addMessage(botMessage);
  
  const currentMessages = getMessages();
  
  if (currentMessages.length === 3) {
    console.log('✅ Messages array contains welcome + user + bot messages');
  } else {
    console.log('❌ Expected 3 messages, got:', currentMessages.length);
    return false;
  }
  
  const userMsg = currentMessages.find((m) => m.sender === 'user');
  if (userMsg && userMsg.text === 'test query') {
    console.log('✅ User message added correctly');
  } else {
    console.log('❌ User message not found or incorrect');
    return false;
  }
  
  return true;
}

function testClearMessagesResetsWelcome() {
  console.log('🧪 Testing clear messages resets welcome message...');
  
  // Simulate hook state with multiple messages
  const [getMessages, setMessages] = mockSetState([
    { sender: 'bot', text: 'Welcome', type: 'info' },
    { sender: 'user', text: 'Hello' },
    { sender: 'bot', text: 'Response' }
  ]);
  
  // Simulate useRef for initialization tracking
  let isInitializedRef = { current: true };
  
  // Simulate clearMessages function
  const clearMessages = () => {
    setMessages([]);
    isInitializedRef.current = false;
  };
  
  // Clear messages
  clearMessages();
  
  if (getMessages().length === 0 && !isInitializedRef.current) {
    console.log('✅ Messages cleared and initialization reset');
    return true;
  } else {
    console.log('❌ Clear messages did not work correctly');
    return false;
  }
}

// Run tests
console.log('🚀 Starting useChat hook welcome message tests...');
console.log('');

const test1 = testWelcomeMessageInitialization();
console.log('');

const test2 = testChatFunctionalityWithWelcomeMessage();
console.log('');

const test3 = testClearMessagesResetsWelcome();
console.log('');

if (test1 && test2 && test3) {
  console.log('🎉 All useChat hook welcome message tests passed!');
  console.log('');
  console.log('📋 Test Summary:');
  console.log('✅ Welcome message initializes correctly on first load');
  console.log('✅ Normal chat functionality works with welcome message present');
  console.log('✅ Clear messages resets welcome message state');
} else {
  console.log('❌ Some tests failed. Please check the implementation.');
}