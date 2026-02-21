import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { FiMessageCircle, FiX, FiSend, FiBook, FiLoader } from 'react-icons/fi';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

// Azora - AI Librarian for the 3D Library - helps users find books
export default function AILibrarian({ books = [], isVisible = true, onCallAzora }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hello! I'm Azora, your magical library guide! ✨ I can help you find the perfect book, tell you about any story in our collection, or answer questions. What would you like to explore today?"
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Build context about available books
  const buildBooksContext = () => {
    if (books.length === 0) return "There are many wonderful books in this library.";
    
    const bookList = books.slice(0, 20).map(book => 
      `- "${book.title}" by ${book.author_name || 'Unknown'} (${book.genre || 'Fiction'}): ${book.description?.slice(0, 100) || 'A wonderful story...'}`
    ).join('\n');
    
    return `Here are some books in our library:\n${bookList}`;
  };

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Send message to AI
  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      // Build system prompt with book context
      const systemPrompt = `You are Azora, a friendly and magical AI librarian assistant in a beautiful digital library called Azories. You are a young witch with magical powers who loves books. You are designed to help children and young readers.

Your personality:
- Warm, encouraging, and slightly whimsical
- You speak simply but not in a condescending way
- You love books and get excited when recommending them
- You use occasional gentle emojis (✨📚🌟)

Your capabilities:
- Help users find books based on their interests
- Describe any book in the library
- Answer questions about stories, characters, or themes
- Suggest books similar to ones they've enjoyed
- Make reading feel like a magical adventure

${buildBooksContext()}

Rules:
- Keep responses concise (2-3 sentences usually)
- Be helpful and positive
- If asked about a book not in the library, suggest similar ones that are
- Never give inappropriate content
- Encourage reading and imagination`;

      const response = await axios.post(`${API}/api/ai/reading-buddy`, {
        message: userMessage,
        system_prompt: systemPrompt,
        context: `User is exploring the 3D library. Previous conversation: ${messages.slice(-4).map(m => `${m.role}: ${m.content}`).join(' | ')}`
      });

      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.data.response || "I'm having trouble thinking right now. Could you try asking again?" 
      }]);
    } catch (error) {
      console.error('AI Librarian error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "Oh dear, I seem to have gotten lost in the shelves! 📚 Could you ask me again?" 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Quick suggestion buttons
  const suggestions = [
    "What book should I read?",
    "Tell me about fantasy books",
    "I want an adventure story",
    "What's popular right now?"
  ];

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-4 left-4 z-50 pointer-events-auto">
      {/* Chat button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
          >
            <Button
              onClick={() => setIsOpen(true)}
              className="w-14 h-14 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 shadow-lg shadow-purple-500/30"
              data-testid="ai-librarian-btn"
            >
              <div className="relative">
                <FiMessageCircle className="w-6 h-6" />
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-white animate-pulse" />
              </div>
            </Button>
            <p className="text-center text-xs text-white/80 mt-1 font-medium">Azora</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Chat window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            className="absolute bottom-0 left-0 bg-gradient-to-br from-[#2d1f3d] to-[#1a1520] rounded-2xl shadow-2xl w-80 max-h-[500px] flex flex-col border border-purple-500/30"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-purple-500/20 bg-purple-500/10">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center">
                  <span className="text-lg">✨</span>
                </div>
                <div>
                  <h3 className="font-semibold text-white">Azora</h3>
                  <p className="text-xs text-purple-300">Library Guide</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsOpen(false)}
                className="text-white/60 hover:text-white hover:bg-white/10 rounded-full"
              >
                <FiX className="w-5 h-5" />
              </Button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[250px]">
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-2 ${
                      msg.role === 'user'
                        ? 'bg-purple-600 text-white rounded-br-md'
                        : 'bg-white/10 text-white/90 rounded-bl-md'
                    }`}
                  >
                    <p className="text-sm leading-relaxed">{msg.content}</p>
                  </div>
                </motion.div>
              ))}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-white/10 rounded-2xl rounded-bl-md px-4 py-3">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Quick suggestions (show only at start) */}
            {messages.length <= 2 && (
              <div className="px-4 pb-2">
                <div className="flex flex-wrap gap-2">
                  {suggestions.map((suggestion, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        setInput(suggestion);
                        setTimeout(() => sendMessage(), 100);
                      }}
                      className="text-xs px-3 py-1.5 rounded-full bg-purple-500/20 text-purple-300 hover:bg-purple-500/30 transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input */}
            <div className="p-3 border-t border-purple-500/20">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  placeholder="Ask Azora anything..."
                  className="flex-1 bg-white/10 border border-purple-500/30 rounded-full px-4 py-2 text-sm text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                  disabled={isLoading}
                />
                <Button
                  onClick={sendMessage}
                  disabled={isLoading || !input.trim()}
                  className="w-10 h-10 rounded-full bg-purple-600 hover:bg-purple-700 disabled:opacity-50"
                >
                  {isLoading ? (
                    <FiLoader className="w-4 h-4 animate-spin" />
                  ) : (
                    <FiSend className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
