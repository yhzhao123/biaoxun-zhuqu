/**
 * AnalysisChatPage - 招标信息分析对话页面
 */
import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { llmService } from '../services/llmApi';
import type { ChatConversation, ChatMessage, LLMConfig } from '../types/llm';

export const AnalysisChatPage: React.FC = () => {
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<ChatConversation | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingConversations, setLoadingConversations] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [llmConfig, setLlmConfig] = useState<LLMConfig | null>(null);
  const [showSidebar, setShowSidebar] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchConversations();
    fetchDefaultConfig();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchConversations = async () => {
    try {
      setLoadingConversations(true);
      const data = await llmService.getConversations();
      setConversations(data);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    } finally {
      setLoadingConversations(false);
    }
  };

  const fetchDefaultConfig = async () => {
    try {
      const config = await llmService.getDefaultConfig();
      setLlmConfig(config);
    } catch (err) {
      console.error('Failed to load default config:', err);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const createNewConversation = async () => {
    try {
      const newConv = await llmService.createConversation('新对话');
      setConversations([newConv, ...conversations]);
      setCurrentConversation(newConv);
      setMessages([]);
    } catch (err) {
      setError('创建对话失败');
    }
  };

  const selectConversation = async (conv: ChatConversation) => {
    try {
      const fullConv = await llmService.getConversation(conv.id!);
      setCurrentConversation(fullConv);
      setMessages(fullConv.messages || []);
    } catch (err) {
      setError('加载对话失败');
    }
  };

  const deleteConversation = async (id: number) => {
    if (!confirm('确定要删除这个对话吗？')) return;
    try {
      await llmService.deleteConversation(id);
      setConversations(conversations.filter(c => c.id !== id));
      if (currentConversation?.id === id) {
        setCurrentConversation(null);
        setMessages([]);
      }
    } catch (err) {
      setError('删除对话失败');
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !currentConversation) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');

    // 添加用户消息到本地
    const newUserMessage: ChatMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    };
    setMessages([...messages, newUserMessage]);
    setLoading(true);

    try {
      const response = await llmService.sendMessage(currentConversation.id!, userMessage);

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.message,
        timestamp: new Date().toISOString(),
        metadata: {
          extracted_entities: response.extracted_entities,
        },
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      setError('发送消息失败');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const analyzeSampleTender = () => {
    const sampleContent = `项目名称：北京市智慧政务平台建设项目
招标人：北京市政务服务中心
预算金额：500万元
项目概况：建设统一的智慧政务服务平台，实现一网通办。
投标截止日期：2024年12月31日
行业：信息技术`;

    setInputMessage(`请分析以下招标信息：\n\n${sampleContent}`);
  };

  const getProviderIcon = (provider?: string) => {
    switch (provider) {
      case 'ollama':
        return '🤖';
      case 'openai':
        return '🧠';
      case 'claude':
        return '📝';
      default:
        return '💬';
    }
  };

  return (
    <div className="h-[calc(100vh-140px)] flex">
      {/* Sidebar - Conversation List */}
      {showSidebar && (
        <div className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-900">对话历史</h2>
              <button
                onClick={createNewConversation}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                + 新建
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            {loadingConversations ? (
              <div className="p-4 text-center text-gray-500 text-sm">加载中...</div>
            ) : conversations.length === 0 ? (
              <div className="p-4 text-center text-gray-500 text-sm">暂无对话</div>
            ) : (
              conversations.map(conv => (
                <div
                  key={conv.id}
                  onClick={() => selectConversation(conv)}
                  className={`p-3 cursor-pointer hover:bg-gray-100 border-b border-gray-100 ${
                    currentConversation?.id === conv.id ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-900 truncate flex-1">
                      {conv.title}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        conv.id && deleteConversation(conv.id);
                      }}
                      className="text-gray-400 hover:text-red-500 ml-2"
                    >
                      ×
                    </button>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {conv.messages?.length || 0} 条消息
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="text-gray-500 hover:text-gray-700"
            >
              {showSidebar ? '◀' : '▶'}
            </button>
            <Link to="/" className="text-gray-600 hover:text-gray-900">返回</Link>
            <h1 className="text-lg font-semibold text-gray-900">
              {currentConversation?.title || '招标信息分析助手'}
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-500">
              {llmConfig ? (
                <>
                  {getProviderIcon(llmConfig.provider)} {llmConfig.name}
                </>
              ) : (
                <span className="text-orange-500">⚠️ 未配置LLM</span>
              )}
            </span>
            {!currentConversation && (
              <button
                onClick={createNewConversation}
                className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
              >
                开始新对话
              </button>
            )}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border-b border-red-400 text-red-700 px-4 py-2 text-sm">
            {error}
            <button onClick={() => setError(null)} className="ml-2 underline">关闭</button>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {!currentConversation ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <div className="text-4xl mb-4">🤖</div>
              <h2 className="text-xl font-medium mb-2">招标信息分析助手</h2>
              <p className="text-center max-w-md mb-6">
                我可以帮你分析招标信息，提取关键实体，回答关于招标内容的问题。
              </p>
              <div className="flex gap-3">
                <button
                  onClick={createNewConversation}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  开始新对话
                </button>
                <button
                  onClick={analyzeSampleTender}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  分析示例招标
                </button>
              </div>
              {!llmConfig && (
                <div className="mt-6 p-4 bg-orange-50 border border-orange-200 rounded-lg text-sm text-orange-800 max-w-md">
                  <strong>提示：</strong>尚未配置LLM。请先前往
                  <Link to="/llm-config" className="text-blue-600 hover:underline">大模型配置</Link>
                  页面设置。
                </div>
              )}
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <div className="text-4xl mb-4">💬</div>
              <p>发送消息开始对话</p>
              <div className="mt-4 flex gap-2">
                <button
                  onClick={() => setInputMessage('请分析这个招标项目的招标人和预算金额')}
                  className="px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200"
                >
                  提取关键信息
                </button>
                <button
                  onClick={() => setInputMessage('这个项目的投标截止日期是什么时候？')}
                  className="px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200"
                >
                  询问截止日期
                </button>
                <button
                  onClick={() => setInputMessage('请给出这个招标项目的合作建议')}
                  className="px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200"
                >
                  合作建议
                </button>
              </div>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-3/4 rounded-lg px-4 py-2 ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
                  {msg.metadata?.extracted_entities && (
                    <div className="mt-2 pt-2 border-t border-gray-200">
                      <div className="text-xs font-medium text-gray-500 mb-1">提取的实体：</div>
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(msg.metadata.extracted_entities).map(([key, value]) => (
                          <span
                            key={key}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-800"
                          >
                            {key}: {String(value)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {msg.timestamp && (
                    <div className={`text-xs mt-1 ${msg.role === 'user' ? 'text-blue-200' : 'text-gray-400'}`}>
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        {currentConversation && (
          <div className="border-t border-gray-200 p-4 bg-white">
            <div className="flex gap-2">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={llmConfig ? '输入消息...' : '请先配置LLM'}
                disabled={!llmConfig || loading}
                className="flex-1 px-4 py-2 border rounded-lg resize-none h-20 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              />
              <button
                onClick={sendMessage}
                disabled={!inputMessage.trim() || loading || !llmConfig}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? '发送中...' : '发送'}
              </button>
            </div>
            <div className="mt-2 text-xs text-gray-500 flex justify-between">
              <span>按 Enter 发送，Shift + Enter 换行</span>
              <Link to="/llm-config" className="text-blue-600 hover:underline">
                配置LLM
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisChatPage;
