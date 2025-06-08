"use client";

import React, { useState, useEffect, useRef } from 'react';
import Header from "../components/Header";
import Footer from "../components/Footer";

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface UIEvent {
  type: string;
  data: any;
  timestamp: string;
}

export default function FastAPIChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isWaitingForInput, setIsWaitingForInput] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<string>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const connectWebSocket = (convId: string) => {
    setConnectionStatus('connecting');
    const ws = new WebSocket(`ws://localhost:8000/ws/${convId}`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setConnectionStatus('connected');
    };
    
    ws.onmessage = (event) => {
      try {
        const uiEvent: UIEvent = JSON.parse(event.data);
        console.log('Received WebSocket event:', uiEvent);
        handleUIEvent(uiEvent);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      setIsLoading(false);
      setConnectionStatus('disconnected');
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
      setIsLoading(false);
      setConnectionStatus('error');
    };
    
    wsRef.current = ws;
  };

  const handleUIEvent = (event: UIEvent) => {
    console.log('Processing event:', event.type, event);
    
    switch (event.type) {
      case 'message':
        const newMessage: Message = {
          id: Date.now().toString(),
          role: event.data.role,
          content: event.data.content,
          timestamp: event.timestamp
        };
        setMessages(prev => [...prev, newMessage]);
        break;
        
      case 'input_request':
        setIsWaitingForInput(true);
        setIsLoading(false);
        // Add the prompt as a message
        const promptMessage: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: event.data.prompt,
          timestamp: event.timestamp
        };
        setMessages(prev => [...prev, promptMessage]);
        break;
        
      case 'tool_call':
        // Show tool execution
        const toolMessage: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `🔧 Executing tool: ${event.data.tool_name || event.data.toolName || 'Unknown tool'}`,
          timestamp: event.timestamp
        };
        setMessages(prev => [...prev, toolMessage]);
        break;
        
      case 'conversation_end':
        setIsWaitingForInput(false);
        setIsLoading(false);
        const endMessage: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: "Thank you for using our travel planning service! 🎉",
          timestamp: event.timestamp
        };
        setMessages(prev => [...prev, endMessage]);
        break;
        
      case 'error':
        setIsWaitingForInput(false);
        setIsLoading(false);
        const errorMessage: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `❌ Error: ${event.data.error}`,
          timestamp: event.timestamp
        };
        setMessages(prev => [...prev, errorMessage]);
        break;
        
      default:
        console.log('Unhandled event type:', event.type);
        break;
    }
  };

  const startConversation = async () => {
    if (!inputValue.trim()) return;
    
    setIsLoading(true);
    setConnectionStatus('starting');
    
    try {
      console.log('Starting conversation with message:', inputValue);
      
      const response = await fetch('http://localhost:8000/api/start_conversation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          initial_message: inputValue
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      const newConversationId = data.conversation_id;
      
      console.log('Conversation started with ID:', newConversationId);
      setConversationId(newConversationId);
      
      // Add user message
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: inputValue,
        timestamp: new Date().toISOString()
      };
      setMessages([userMessage]);
      setInputValue('');
      
      // Connect WebSocket
      connectWebSocket(newConversationId);
      
    } catch (error) {
      console.error('Error starting conversation:', error);
      setIsLoading(false);
      setConnectionStatus('error');
      
      // Show error message
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `❌ Failed to start conversation: ${error}`,
        timestamp: new Date().toISOString()
      };
      setMessages([errorMessage]);
    }
  };

  const sendUserInput = () => {
    if (!inputValue.trim() || !wsRef.current || !isWaitingForInput) return;
    
    console.log('Sending user input:', inputValue);
    
    // Add user message to chat
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    
    // Send through WebSocket
    wsRef.current.send(JSON.stringify({
      type: 'user_input',
      content: inputValue
    }));
    
    setInputValue('');
    setIsWaitingForInput(false);
    setIsLoading(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!conversationId) {
      startConversation();
    } else if (isWaitingForInput) {
      sendUserInput();
    }
  };

  const resetConversation = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    setMessages([]);
    setConversationId(null);
    setIsConnected(false);
    setIsWaitingForInput(false);
    setIsLoading(false);
    setInputValue('');
    setConnectionStatus('disconnected');
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'bg-green-400';
      case 'connecting': return 'bg-yellow-400';
      case 'starting': return 'bg-blue-400';
      case 'error': return 'bg-red-400';
      default: return 'bg-gray-400';
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connected';
      case 'connecting': return 'Connecting...';
      case 'starting': return 'Starting...';
      case 'error': return 'Error';
      default: return 'Disconnected';
    }
  };

  return (
    <div className="min-h-screen flex flex-col font-[family-name:var(--font-geist-sans)]">
      <Header />
      
      <main className="flex-1 container mx-auto px-4 py-8 max-w-4xl">
        <div className="bg-white rounded-lg shadow-lg h-[70vh] flex flex-col">
          {/* Chat Header */}
          <div className="bg-blue-600 text-white p-4 rounded-t-lg flex justify-between items-center">
            <h1 className="text-xl font-bold">Travel Planning Assistant (FastAPI)</h1>
            <div className="flex items-center gap-4">
              <span className={`w-3 h-3 rounded-full ${getConnectionStatusColor()}`} />
              <span className="text-sm">{getConnectionStatusText()}</span>
              {conversationId && (
                <button
                  onClick={resetConversation}
                  className="bg-blue-500 hover:bg-blue-400 px-3 py-1 rounded text-sm"
                >
                  New Chat
                </button>
              )}
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 mt-8">
                <h2 className="text-2xl font-bold mb-4">Welcome to Travel AI! ✈️</h2>
                <p className="text-lg mb-4">
                  I'm here to help you plan your perfect trip. Start by telling me about your travel plans!
                </p>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
                  <p className="text-sm text-blue-600 font-medium mb-2">💡 Quick Start Tips:</p>
                  <ul className="text-sm text-blue-600 space-y-1">
                    <li>• Try: "I want to plan a trip to Paris for 3 days"</li>
                    <li>• Use member IDs: P12345 (premium) or S12345 (standard)</li>
                    <li>• When asked for permission, type "continue" to proceed</li>
                  </ul>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 text-gray-800'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    <p className="text-xs opacity-70 mt-1">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))
            )}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-200 text-gray-800 px-4 py-2 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin h-4 w-4 border-2 border-blue-500 rounded-full border-t-transparent"></div>
                    <span>Agent is thinking...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t p-4">
            <form onSubmit={handleSubmit} className="flex space-x-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={
                  !conversationId 
                    ? "Start your travel planning journey..." 
                    : isWaitingForInput 
                      ? "Type your response..." 
                      : "Waiting for assistant..."
                }
                className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading || (conversationId && !isWaitingForInput)}
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || isLoading || (conversationId && !isWaitingForInput)}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-2 rounded-lg font-medium transition-colors"
              >
                {!conversationId ? 'Start' : 'Send'}
              </button>
            </form>
            
            {isWaitingForInput && (
              <p className="text-sm text-blue-600 mt-2">
                💡 The assistant is waiting for your response
              </p>
            )}
            
            {connectionStatus === 'error' && (
              <p className="text-sm text-red-600 mt-2">
                ⚠️ Connection error. Please check if the backend is running on localhost:8000
              </p>
            )}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
