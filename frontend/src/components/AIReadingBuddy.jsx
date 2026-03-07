import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { FiMessageCircle, FiX, FiSend, FiBook, FiHelpCircle, FiZap } from 'react-icons/fi';
import { aiAPI, getErrorMessage } from '../services/api';

// Suggested questions based on reading context
const SUGGESTED_QUESTIONS = [
  { icon: '🔮', text: "What might happen next?" },
  { icon: '🎭', text: "Tell me about the main character" },
  { icon: '📖', text: "Summarize what I've read so far" },
  { icon: '🤔', text: "Explain this part to me" },
  { icon: '✨', text: "What's the theme of this story?" },
];

export default function AIReadingBuddy({ book, currentPage, isOpen, onToggle }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Detect mobile viewport (including mobile landscape)
  useEffect(() => {
    const checkMobile = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      // Hide on mobile portrait OR mobile landscape (small height indicates rotated phone)
      const isMobilePortrait = width < 768;
      const isMobileLandscape = height < 500 && width < 900;
      setIsMobile(isMobilePortrait || isMobileLandscape);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Initialize with welcome message
  useEffect(() => {
    if (isOpen && messages.length === 0 && book) {
      setMessages([{
        id: 'welcome',
        role: 'assistant',
        content: `Hi! I'm your reading buddy for "${book.title}". I can help you understand the story, predict what happens next, or just chat about what you're reading! What would you like to know?`
      }]);
    }
  }, [isOpen, book, messages.length]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && !isMinimized) {
      inputRef.current?.focus();
    }
  }, [isOpen, isMinimized]);

  const getBookContext = () => {
    if (!book || !book.pages) return '';
    
    // Get content from pages up to current page
    const readPages = book.pages.slice(0, currentPage + 1);
    const content = readPages
      .filter(p => p.text)
      .map(p => p.text)
      .join('\n\n');
    
    return content.slice(-3000); // Last 3000 chars for context
  };

  const sendMessage = async (text = input) => {
    if (!text.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text.trim()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const bookContext = getBookContext();
      
      const response = await aiAPI.readingBuddy({
        book_id: book.id,
        book_title: book.title,
        book_genre: book.genre,
        current_page: currentPage,
        book_context: bookContext,
        question: text.trim(),
        chat_history: messages.slice(-6).map(m => ({
          role: m.role,
          content: m.content
        }))
      });

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.response
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('AI Reading Buddy error:', error);
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "Oops! I had trouble thinking about that. Could you try asking in a different way?"
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!isOpen) {
    // Hide the floating button on mobile to not overlap reading content
    if (isMobile) {
      return null;
    }
    
    return (
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={onToggle}
        className="fixed bottom-28 left-4 z-[110] w-14 h-14 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full shadow-lg flex items-center justify-center text-white"
        data-testid="ai-buddy-toggle"
      >
        <FiMessageCircle className="w-6 h-6" />
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white animate-pulse" />
      </motion.button>
    );
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 100, scale: 0.9 }}
        animate={{ 
          opacity: 1, 
          y: 0, 
          scale: 1,
          height: isMinimized ? 'auto' : '500px'
        }}
        exit={{ opacity: 0, y: 100, scale: 0.9 }}
        className="fixed bottom-4 left-4 z-[110] w-80 sm:w-96 bg-background border rounded-2xl shadow-2xl overflow-hidden flex flex-col"
        data-testid="ai-buddy-panel"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-4 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                <FiZap className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold">Reading Buddy</h3>
                <p className="text-xs text-white/70">AI-powered assistant</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="p-2 hover:bg-white/20 rounded-full transition-colors"
              >
                <div className={`w-4 h-0.5 bg-white transition-transform ${isMinimized ? 'rotate-0' : ''}`} />
              </button>
              <button
                onClick={onToggle}
                className="p-2 hover:bg-white/20 rounded-full transition-colors"
              >
                <FiX className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {!isMinimized && (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] p-3 rounded-2xl ${
                      message.role === 'user'
                        ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-br-md'
                        : 'bg-muted rounded-bl-md'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  </div>
                </motion.div>
              ))}
              
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-start"
                >
                  <div className="bg-muted p-3 rounded-2xl rounded-bl-md">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </motion.div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Suggested Questions */}
            {messages.length <= 2 && (
              <div className="px-4 pb-2">
                <p className="text-xs text-muted-foreground mb-2">Try asking:</p>
                <div className="flex flex-wrap gap-2">
                  {SUGGESTED_QUESTIONS.slice(0, 3).map((q, i) => (
                    <button
                      key={i}
                      onClick={() => sendMessage(q.text)}
                      className="px-3 py-1.5 bg-muted hover:bg-muted/80 rounded-full text-xs flex items-center gap-1 transition-colors"
                    >
                      <span>{q.icon}</span>
                      <span className="truncate max-w-[120px]">{q.text}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input */}
            <div className="p-4 border-t">
              <div className="flex gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about the story..."
                  className="flex-1 px-4 py-2 bg-muted rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  disabled={isLoading}
                />
                <Button
                  onClick={() => sendMessage()}
                  disabled={!input.trim() || isLoading}
                  size="icon"
                  className="rounded-full bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90"
                >
                  <FiSend className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
