// 简单的前端逻辑：连接 Stable Diffusion WebUI 的 REST API

// ======== 工具函数 ========
function getApiBaseUrl() {
  // 允许用户在设置里自定义 API 地址，默认为本机
  const input = document.getElementById('api-url');
  const saved = localStorage.getItem('sd_api_url');
  if (input && !input.value && saved) {
    input.value = saved;
  }
  const value = (input && input.value) || saved || 'http://127.0.0.1:7860';
  return value.replace(/\/+$/, ''); // 去掉末尾斜杠
}

function saveApiBaseUrl() {
  const input = document.getElementById('api-url');
  if (!input) return;
  const value = input.value.trim();
  if (value) {
    localStorage.setItem('sd_api_url', value);
  }
}

function showImageLoading(show) {
  const loading = document.getElementById('image-loading');
  if (!loading) return;
  if (show) {
    loading.classList.remove('hidden');
  } else {
    loading.classList.add('hidden');
  }
}

function clearImageOutput() {
  const output = document.getElementById('image-output');
  if (!output) return;
  output.innerHTML = `
    <div class="empty-preview">
      <div class="preview-icon">🖼️</div>
      <p>生成的图片将显示在这里</p>
    </div>
  `;
}

function appendHistoryItem(prompt, style, size) {
  const history = document.getElementById('image-history');
  if (!history) return;
  // 去除空状态
  const empty = history.querySelector('.empty-state');
  if (empty) empty.remove();

  const item = document.createElement('div');
  item.className = 'history-item';
  item.innerHTML = `
    <div class="history-text">${prompt ? prompt.replace(/</g, '&lt;') : '（无描述）'}</div>
    <div class="history-meta">
      <span>${style}</span>
      <span>${size}</span>
      <span>${new Date().toLocaleTimeString()}</span>
    </div>
  `;
  history.prepend(item);
}

async function callTxt2Img(prompt, style, width, height, batchSize, steps = 20) {
  const base = getApiBaseUrl();
  const url = `${base}/sdapi/v1/txt2img`;

  // 可以根据风格拼一些简单的提示词，这里只是示例
  let stylePrompt = '';
  switch (style) {
    case 'anime':
      stylePrompt = ', anime style, 2d, highly detailed';
      break;
    case 'oil-painting':
      stylePrompt = ', oil painting, textured, artstation';
      break;
    case 'watercolor':
      stylePrompt = ', watercolor, soft, light colors';
      break;
    case 'sketch':
      stylePrompt = ', pencil sketch, lineart';
      break;
    case 'cyberpunk':
      stylePrompt = ', cyberpunk, neon lights, futuristic';
      break;
    case 'fantasy':
      stylePrompt = ', fantasy, epic, highly detailed';
      break;
    default:
      stylePrompt = '';
  }

  // 确保步数在合理范围内
  const validSteps = Math.max(1, Math.min(150, steps || 20));

  const body = {
    prompt: (prompt || '') + stylePrompt,
    steps: validSteps,
    width,
    height,
    batch_size: batchSize,
  };

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`请求失败: ${res.status} ${text}`);
  }

  const data = await res.json();
  return data.images || [];
}

function renderImages(base64Images) {
  const output = document.getElementById('image-output');
  if (!output) return;

  if (!base64Images.length) {
    clearImageOutput();
    return;
  }

  output.innerHTML = '';
  base64Images.forEach((b64, idx) => {
    const imgWrapper = document.createElement('div');
    imgWrapper.className = 'generated-image-wrapper';

    const img = document.createElement('img');
    img.className = 'generated-image';
    img.src = `data:image/png;base64,${b64}`;
    img.alt = `生成图片 ${idx + 1}`;

    const downloadBtn = document.createElement('button');
    downloadBtn.className = 'icon-btn small';
    downloadBtn.textContent = '⬇️';
    downloadBtn.title = '下载这张图片';
    downloadBtn.addEventListener('click', () => {
      const a = document.createElement('a');
      a.href = img.src;
      a.download = `sd_image_${Date.now()}_${idx + 1}.png`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    });

    imgWrapper.appendChild(img);
    imgWrapper.appendChild(downloadBtn);
    output.appendChild(imgWrapper);
  });
}

function downloadAllImages() {
  const imgs = document.querySelectorAll('#image-output img.generated-image');
  imgs.forEach((img, idx) => {
    const a = document.createElement('a');
    a.href = img.src;
    a.download = `sd_image_${Date.now()}_${idx + 1}.png`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  });
}

// ======== 事件绑定 ========
window.addEventListener('DOMContentLoaded', () => {
  // 初始化：如果首页激活，调整主容器样式
  const homeSection = document.getElementById('home');
  const mainContainer = document.querySelector('.main-container');
  if (homeSection && homeSection.classList.contains('active') && mainContainer) {
    mainContainer.classList.add('home-active');
  }
  
  // 注意：导航链接的点击处理已移至 initNavigation() 函数中，避免重复绑定

  // 初始化图生视频功能
  initImageToVideo();

  // 设置弹窗
  const settingsBtn = document.getElementById('settings-btn');
  const settingsModal = document.getElementById('settings-modal');
  const closeSettings = document.getElementById('close-settings');
  const cancelSettings = document.getElementById('cancel-settings');
  const saveSettings = document.getElementById('save-settings');

  if (settingsBtn && settingsModal) {
    settingsBtn.addEventListener('click', () => {
      // 打开前先填入本地保存的地址
      const input = document.getElementById('api-url');
      const saved = localStorage.getItem('sd_api_url');
      if (input && saved && !input.value) {
        input.value = saved;
      }
      settingsModal.showModal();
    });
  }
  if (closeSettings && settingsModal) {
    closeSettings.addEventListener('click', () => settingsModal.close());
  }
  if (cancelSettings && settingsModal) {
    cancelSettings.addEventListener('click', () => settingsModal.close());
  }
  if (saveSettings && settingsModal) {
    saveSettings.addEventListener('click', () => {
      saveApiBaseUrl();
      settingsModal.close();
    });
  }

  // 图片生成按钮
  const genBtn = document.getElementById('generate-image-btn');
  if (genBtn) {
    genBtn.addEventListener('click', async () => {
      const promptEl = document.getElementById('image-prompt');
      const styleEl = document.getElementById('image-style');
      const sizeEl = document.getElementById('image-size');
      const countEl = document.getElementById('image-count');

      const prompt = promptEl ? promptEl.value.trim() : '';
      const style = styleEl ? styleEl.value : 'realistic';
      const size = sizeEl ? sizeEl.value : '1024x1024';
      const count = countEl ? Number(countEl.value || 1) : 1;

      let width = 1024;
      let height = 1024;
      if (size.includes('x')) {
        const [w, h] = size.split('x').map((v) => parseInt(v, 10));
        if (!isNaN(w) && !isNaN(h)) {
          width = w;
          height = h;
        }
      }

      // 尝试读取采样步数（如果存在）
      const stepsEl = document.getElementById('image-steps');
      const steps = stepsEl ? Number(stepsEl.value || 20) : 20;

      showImageLoading(true);
      try {
        const images = await callTxt2Img(prompt, style, width, height, count, steps);
        renderImages(images);
        appendHistoryItem(prompt, style, `${width}x${height}`);
      } catch (err) {
        console.error(err);
        alert('生成失败：' + err.message);
      } finally {
        showImageLoading(false);
      }
    });
  }

  // 清空图片
  const clearBtn = document.getElementById('clear-image-btn');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      clearImageOutput();
    });
  }

  // 全部下载
  const downloadAllBtn = document.getElementById('download-all-btn');
  if (downloadAllBtn) {
    downloadAllBtn.addEventListener('click', () => {
      downloadAllImages();
    });
  }

  // 数字人模块的一些基础交互（暂时只做前端 UI 切换，真实调用 SadTalker 可以后面补充）
  const modeTabs = document.querySelectorAll('.mode-tab');
  const textMode = document.getElementById('text-mode');
  const uploadMode = document.getElementById('upload-mode');
  modeTabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      modeTabs.forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      const mode = tab.getAttribute('data-mode');
      if (mode === 'text') {
        textMode && textMode.classList.add('active');
        uploadMode && uploadMode.classList.remove('active');
      } else {
        textMode && textMode.classList.remove('active');
        uploadMode && uploadMode.classList.add('active');
      }
    });
  });

  // 语音开关
  const enableVoice = document.getElementById('enable-voice');
  const voiceOptions = document.getElementById('voice-options');
  if (enableVoice && voiceOptions) {
    enableVoice.addEventListener('change', () => {
      if (enableVoice.checked) {
        voiceOptions.classList.remove('hidden');
      } else {
        voiceOptions.classList.add('hidden');
      }
    });
  }

  // 初始化默认 API 地址显示
  const apiInput = document.getElementById('api-url');
  if (apiInput && !apiInput.value) {
    const saved = localStorage.getItem('sd_api_url');
    apiInput.value = saved || 'http://127.0.0.1:7860';
  }
});

// ========== 配置区域 ==========
// 在这里填写你的 API Key（可选）
// 如果在这里填写，会作为默认值使用
// 你也可以在设置界面中配置，设置界面的配置会覆盖这里的值
const DEEPSEEK_API_KEY = 'YOUR_DEEPSEEK_API_KEY'; // 在这里填写你的 DeepSeek API Key，例如: 'sk-xxxxxxxxxxxxx'
const KLING_ACCESS_KEY = 'YOUR_KLING_ACCESS_KEY'; // 在这里填写你的可灵访问密钥 (Access Key)，不要包含 "Access Key: " 前缀
const KLING_SECRET_KEY = 'YOUR_KLING_SECRET_KEY'; // 在这里填写你的可灵密钥 (Secret Key)

// ========== 全局状态 ==========
const state = {
  // Stable Diffusion WebUI API 地址（需要改为运行 WebUI 的设备IP）
  // 例如: http://192.168.1.100:7860 或 http://localhost:7860
  apiUrl: localStorage.getItem('apiUrl') || 'http://localhost:7860',
  // DeepSeek API Key（用于 AI 助手功能）
  // 优先使用 localStorage 中的值，如果没有则使用上面配置的 DEEPSEEK_API_KEY
  deepseekApiKey: localStorage.getItem('deepseekApiKey') || DEEPSEEK_API_KEY,
  // 可灵 API 密钥（用于图生视频功能）
  // 优先使用 localStorage 中的值，如果没有则使用上面配置的值
  klingAccessKey: localStorage.getItem('klingAccessKey') || KLING_ACCESS_KEY,
  klingSecretKey: localStorage.getItem('klingSecretKey') || KLING_SECRET_KEY,
  imageHistory: JSON.parse(localStorage.getItem('imageHistory') || '[]'),
  humanGallery: JSON.parse(localStorage.getItem('humanGallery') || '[]'),
  currentMode: 'text' // 'text' 或 'upload'
};

// DOM 元素
const elements = {
  // 导航
  navLinks: document.querySelectorAll('.nav-link'),
  sections: document.querySelectorAll('.feature-section'),
  
  // 图片生成
  imagePrompt: document.getElementById('image-prompt'),
  imageNegativePrompt: document.getElementById('image-negative-prompt'),
  imageStyle: document.getElementById('image-style'),
  loraSelect: document.getElementById('lora-select'),
  loraWeight: document.getElementById('lora-weight'),
  imageSize: document.getElementById('image-size'),
  imageCount: document.getElementById('image-count'),
  imageSteps: document.getElementById('image-steps'),
  generateImageBtn: document.getElementById('generate-image-btn'),
  imageOutput: document.getElementById('image-output'),
  imageLoading: document.getElementById('image-loading'),
  imageHistory: document.getElementById('image-history'),
  clearImageBtn: document.getElementById('clear-image-btn'),
  downloadAllBtn: document.getElementById('download-all-btn'),
  
  // 数字人生成
  humanPrompt: document.getElementById('human-prompt'),
  humanType: document.getElementById('human-type'),
  humanStyle: document.getElementById('human-style'),
  humanAge: document.getElementById('human-age'),
  generateHumanBtn: document.getElementById('generate-human-btn'),
  humanOutput: document.getElementById('human-output'),
  humanLoading: document.getElementById('human-loading'),
  humanGallery: document.getElementById('human-gallery'),
  animateHumanBtn: document.getElementById('animate-human-btn'),
  downloadHumanBtn: document.getElementById('download-human-btn'),
  
  // 模式切换
  modeTabs: document.querySelectorAll('.mode-tab'),
  textMode: document.getElementById('text-mode'),
  uploadMode: document.getElementById('upload-mode'),
  imageUploadArea: document.getElementById('image-upload-area'),
  humanImageInput: document.getElementById('human-image-input'),
  uploadedPreview: document.getElementById('uploaded-preview'),
  
  // 语音合成
  enableVoice: document.getElementById('enable-voice'),
  voiceOptions: document.getElementById('voice-options'),
  voiceText: document.getElementById('voice-text'),
  voiceType: document.getElementById('voice-type'),
  generateVoiceBtn: document.getElementById('generate-voice-btn'),
  
  // 音频克隆
  voiceCloneText: document.getElementById('voice-text'), // 注意：与数字人模块的 voiceText 可能冲突，但数字人模块的 voiceText 可能不存在
  voiceMode: document.getElementById('voice-mode'),
  voicePromptUpload: document.getElementById('voice-prompt-upload'),
  voicePromptRecord: document.getElementById('voice-prompt-record'),
  voicePromptPreview: document.getElementById('voice-prompt-preview'),
  voicePromptPlayer: document.getElementById('voice-prompt-player'),
  voicePromptText: document.getElementById('voice-prompt-text'),
  voiceInstructText: document.getElementById('voice-instruct-text'),
  voiceSeed: document.getElementById('voice-seed'),
  voiceGenerateSeed: document.getElementById('voice-generate-seed'),
  voiceStream: document.getElementById('voice-stream'),
  voiceGenerateBtn: document.getElementById('voice-generate-btn'),
  voiceOutput: document.getElementById('voice-output'),
  voiceLoading: document.getElementById('voice-loading'),
  voiceClearBtn: document.getElementById('voice-clear-btn'),
  voiceDownloadBtn: document.getElementById('voice-download-btn'),
  voiceInstruction: document.getElementById('voice-instruction'),
  voiceRecognizeBtn: document.getElementById('voice-recognize-btn'),
  
  // 图生视频
  videoImageInput: document.getElementById('video-image-input'),
  videoImageUploadArea: document.getElementById('video-image-upload-area'),
  videoUploadedPreview: document.getElementById('video-uploaded-preview'),
  videoAnimationType: document.getElementById('video-animation-type'),
  videoDuration: document.getElementById('video-duration'),
  videoDurationValue: document.getElementById('video-duration-value'),
  videoFps: document.getElementById('video-fps'),
  videoResolution: document.getElementById('video-resolution'),
  videoStrength: document.getElementById('video-strength'),
  videoStrengthValue: document.getElementById('video-strength-value'),
  videoPrompt: document.getElementById('video-prompt'),
  videoNegativePrompt: document.getElementById('video-negative-prompt'),
  videoLoop: document.getElementById('video-loop'),
  generateVideoBtn: document.getElementById('generate-video-btn'),
  videoOutput: document.getElementById('video-output'),
  videoLoading: document.getElementById('video-loading'),
  
  // 设置
  settingsBtn: document.getElementById('settings-btn'),
  settingsModal: document.getElementById('settings-modal'),
  closeSettings: document.getElementById('close-settings'),
  cancelSettings: document.getElementById('cancel-settings'),
  saveSettings: document.getElementById('save-settings'),
  apiUrlInput: document.getElementById('api-url'),
  defaultQuality: document.getElementById('default-quality'),
  deepseekApiKeyInput: document.getElementById('deepseek-api-key'),
  klingAccessKeyInput: document.getElementById('kling-access-key'),
  klingSecretKeyInput: document.getElementById('kling-secret-key'),
  
  // SadTalker 设置
  poseStyle: document.getElementById('pose-style'),
  poseStyleValue: document.getElementById('pose-style-value'),
  faceResolution: document.querySelectorAll('input[name="face-resolution"]'),
  preprocess: document.getElementById('preprocess'),
  stillMode: document.getElementById('still-mode'),
  batchSize: document.getElementById('batch-size'),
  batchSizeValue: document.getElementById('batch-size-value'),
  gfpganEnhancer: document.getElementById('gfpgan-enhancer'),
  
  // AI 聊天
  chatSidebar: document.getElementById('ai-chat-sidebar'),
  chatToggleBtn: document.getElementById('chat-toggle-btn'),
  chatCloseBtn: document.getElementById('chat-close-btn'),
  chatClearBtn: document.getElementById('chat-clear-btn'),
  chatMessages: document.getElementById('chat-messages'),
  chatInput: document.getElementById('chat-input'),
  deepseekApiKeyInput: document.getElementById('deepseek-api-key'),
  chatSendBtn: document.getElementById('chat-send-btn'),
  chatTabs: document.querySelectorAll('.chat-tab'),
  quickActionBtns: document.querySelectorAll('.quick-action-btn')
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
  try {
    console.log('🚀 开始初始化应用...');
  initNavigation();
  initImageGeneration();
    initVoiceClone();
  initDigitalHuman();
    initImageToVideo();
  initSettings();
  loadHistory();
  loadGallery();
    console.log('✅ 应用初始化完成');
  } catch (error) {
    console.error('❌ 应用初始化失败:', error);
    console.error('错误堆栈:', error.stack);
    alert('应用初始化失败，请查看控制台获取详细信息');
  }
});

// 导航切换
function initNavigation() {
  const homeSection = document.getElementById('home');
  const allSections = document.querySelectorAll('section[id]'); // 获取所有有 id 的 section
  const navLinks = document.querySelectorAll('.nav-link');
  
  // 处理导航链接点击
  console.log('initNavigation: 找到导航链接数量:', navLinks.length);
  
  navLinks.forEach((link, index) => {
    const href = link.getAttribute('href');
    console.log(`initNavigation: 处理导航链接 ${index}，href:`, href, 'id:', link.id);
    
    // 如果是外部链接（http/https）或新页面（.html），让浏览器默认行为处理
    if (href && (href.startsWith('http://') || href.startsWith('https://') || href.endsWith('.html'))) {
      console.log(`initNavigation: 跳过外部链接或新页面 ${index}:`, href, '（让浏览器处理跳转）');
      // 确保链接可点击
      link.style.cursor = 'pointer';
      return; // 不绑定事件，让浏览器默认行为处理
    }
    
    // 如果是 target="_blank" 的外部链接，也跳过
    if (link.getAttribute('target') === '_blank') {
      console.log(`initNavigation: 跳过新窗口链接 ${index}:`, href);
      link.style.cursor = 'pointer';
      return;
    }
    
    // 绑定点击事件（仅用于内部 section 切换，如 #home, #image-gen 等）
    link.addEventListener('click', (e) => {
      console.log('✅ 导航链接被点击，href:', href, '链接文本:', link.textContent);
      
      e.preventDefault();
      e.stopPropagation();
      
      if (!href) {
        console.warn('导航链接没有 href 属性');
        return;
      }
      
      // 检查是否是内部锚点链接（以 # 开头）
      if (!href.startsWith('#')) {
        console.warn('导航链接不是内部锚点，应该使用 .html 文件链接');
        return;
      }
      
      const target = document.querySelector(href);
      if (!target) {
        console.error('❌ 找不到目标 section:', href);
        alert(`找不到目标页面: ${href}`);
        return;
      }
      
      console.log('✅ 找到目标 section:', target.id);
      
      // 更新导航状态
      navLinks.forEach(l => l.classList.remove('active'));
      link.classList.add('active');
      console.log('✅ 已更新导航链接状态:', link.id || link.textContent);
      
      // 隐藏所有 section，显示目标 section
      allSections.forEach(s => s.classList.remove('active'));
      target.classList.add('active');
      console.log('✅ 已显示目标 section:', target.id);
      
      // 更新主容器样式
      const mainContainer = document.querySelector('.main-container');
      if (mainContainer) {
        if (target.id === 'home') {
          mainContainer.classList.add('home-active');
        } else {
          mainContainer.classList.remove('home-active');
        }
      }
      
      // 平滑滚动到顶部
      window.scrollTo({ top: 0, behavior: 'smooth' });
      console.log('✅ 页面切换完成');
    });
    
    // 确保链接可点击
    link.style.cursor = 'pointer';
    console.log(`✅ 已绑定导航链接 ${index}:`, href);
  });
  
  // 处理首页功能卡片点击
  console.log('initNavigation: 开始绑定首页卡片点击事件，homeSection:', homeSection);
  
  // 创建统一的页面切换函数（暴露到全局，方便调试）
  window.switchToPage = function(targetHref) {
    console.log('🔄 切换页面，href:', targetHref);
    
    const target = document.querySelector(targetHref);
    if (!target) {
      console.error('❌ 找不到目标 section:', targetHref);
      alert(`找不到目标页面: ${targetHref}`);
      return false;
    }
    
    console.log('✅ 找到目标 section:', target.id);
    
    // 获取所有 section 和导航链接（重新查询以确保最新）
    const allSectionsList = document.querySelectorAll('section[id]');
    const navLinksList = document.querySelectorAll('.nav-link');
    
    // 隐藏所有 section，显示目标页面
    allSectionsList.forEach((s) => {
      s.classList.remove('active');
    });
    navLinksList.forEach((l) => l.classList.remove('active'));
    
    // 更新主容器样式
    const mainContainer = document.querySelector('.main-container');
    if (mainContainer) {
      if (target.id === 'home') {
        mainContainer.classList.add('home-active');
      } else {
        mainContainer.classList.remove('home-active');
      }
    }
    
    // 显示目标 section
    target.classList.add('active');
    console.log('✅ 已显示目标 section:', target.id);
    
    // 更新对应的导航链接状态
    const correspondingNavLink = document.querySelector(`.nav-link[href="${targetHref}"]`);
    if (correspondingNavLink) {
      correspondingNavLink.classList.add('active');
      console.log('✅ 已更新导航链接状态:', correspondingNavLink.id || correspondingNavLink.textContent);
    } else {
      console.warn('⚠️ 找不到对应的导航链接:', targetHref);
    }
    
    // 平滑滚动到顶部
    window.scrollTo({ top: 0, behavior: 'smooth' });
    console.log('✅ 页面切换完成');
    return true;
  };
  
  // 绑定首页卡片点击事件 - 使用多种方式确保可靠
  function bindHomeCards() {
    // 只在首页（index.html）绑定，其他页面不需要
    if (!window.location.pathname.endsWith('index.html') && !window.location.pathname.endsWith('/')) {
      console.log('⏭️ 跳过首页卡片绑定（不在首页）');
      return;
    }
    
    console.group('🔍 开始绑定首页卡片点击事件');
    
    const homeFeatureCards = document.querySelectorAll('.home-feature-card');
    console.log('📊 找到首页功能卡片数量:', homeFeatureCards.length);
    
    if (homeFeatureCards.length === 0) {
      console.log('⏭️ 未找到首页功能卡片（可能不在首页或元素尚未加载）');
      console.log('  - 当前页面URL:', window.location.href);
      console.log('  - 检查 #home section 是否存在:', !!document.getElementById('home'));
      console.log('  - 检查 .home-features 是否存在:', !!document.querySelector('.home-features'));
      console.log('  - 检查 .home-feature-card 是否存在:', !!document.querySelector('.home-feature-card'));
      console.groupEnd();
      return; // 不再重试，避免无限循环
    }
    
    console.log('✅ 找到卡片，开始绑定事件...');
    
    homeFeatureCards.forEach((card, index) => {
      console.group(`📋 处理卡片 ${index}`);
      
      const href = card.getAttribute('href');
      console.log('  - href 属性:', href);
      console.log('  - 卡片元素:', card);
      console.log('  - 卡片标签名:', card.tagName);
      console.log('  - 卡片类名:', card.className);
      console.log('  - 卡片是否可见:', card.offsetWidth > 0 && card.offsetHeight > 0);
      console.log('  - 卡片位置:', {
        top: card.offsetTop,
        left: card.offsetLeft,
        width: card.offsetWidth,
        height: card.offsetHeight
      });
      
      // 检查CSS样式
      const computedStyle = window.getComputedStyle(card);
      console.log('  - CSS pointer-events:', computedStyle.pointerEvents);
      console.log('  - CSS z-index:', computedStyle.zIndex);
      console.log('  - CSS position:', computedStyle.position);
      console.log('  - CSS display:', computedStyle.display);
      console.log('  - CSS visibility:', computedStyle.visibility);
      console.log('  - CSS opacity:', computedStyle.opacity);
      
      // 检查是否有其他元素覆盖
      const cardRect = card.getBoundingClientRect();
      const elementAtCenter = document.elementFromPoint(
        cardRect.left + cardRect.width / 2,
        cardRect.top + cardRect.height / 2
      );
      console.log('  - 卡片中心位置的元素:', elementAtCenter);
      console.log('  - 是否被其他元素覆盖:', elementAtCenter !== card && !card.contains(elementAtCenter));
      
      if (!href) {
        console.error(`❌ 卡片 ${index} 没有 href 属性`);
        console.groupEnd();
        return;
      }
      
      // 确保卡片可点击
      card.style.cursor = 'pointer';
      card.style.pointerEvents = 'auto';
      card.style.position = 'relative';
      card.style.zIndex = '999';
      console.log('  - 已设置样式: cursor=pointer, pointer-events=auto, z-index=999');
      
      // 移除所有现有的事件监听器（通过设置onclick为null）
      card.onclick = null;
      console.log('  - 已清除旧的onclick事件');
      
      // 方法1: 使用onclick属性（最简单直接）
      card.onclick = function(e) {
        console.group('🖱️ [onclick] 卡片被点击');
        console.log('  - href:', href);
        console.log('  - 卡片索引:', index);
        console.log('  - 点击事件对象:', e);
        console.log('  - 点击位置:', { x: e.clientX, y: e.clientY });
        console.log('  - 目标元素:', e.target);
        console.log('  - 当前目标元素:', e.currentTarget);
        
        // 如果是外部链接（http/https）或新页面（.html），让浏览器默认行为处理
        if (href.startsWith('http://') || href.startsWith('https://') || href.endsWith('.html')) {
          console.log('  - 外部链接或新页面，使用默认行为（浏览器跳转）');
          console.groupEnd();
          return true; // 允许默认行为，让浏览器跳转到新页面
        }
        
        // 如果是内部链接（以#开头），阻止默认行为并切换页面
        e.preventDefault();
        e.stopPropagation();
        console.log('  - 阻止默认行为，查找目标 section:', href);
        
        const target = document.querySelector(href);
        if (!target) {
          console.error('  - ❌ 找不到目标 section:', href);
          console.groupEnd();
          return false;
        }
        
        console.log('  - ✅ 找到目标 section:', target.id);
        const success = window.switchToPage(href);
        if (!success) {
          console.error('  - ❌ 页面切换失败');
        } else {
          console.log('  - ✅ 页面切换成功');
        }
        console.groupEnd();
        return false;
      };
      console.log('  - ✅ 已绑定onclick事件');
      
      // 方法2: 同时使用addEventListener作为备用
      const eventHandler = function(e) {
        console.group('🖱️ [addEventListener] 卡片被点击');
        console.log('  - href:', href);
        console.log('  - 卡片索引:', index);
        console.log('  - 点击事件对象:', e);
        console.log('  - 点击位置:', { x: e.clientX, y: e.clientY });
        console.log('  - 目标元素:', e.target);
        console.log('  - 当前目标元素:', e.currentTarget);
        
        // 如果是外部链接（http/https）或新页面（.html），让浏览器默认行为处理
        if (href.startsWith('http://') || href.startsWith('https://') || href.endsWith('.html')) {
          console.log('  - 外部链接或新页面，使用默认行为（浏览器跳转）');
          console.groupEnd();
          return; // 不阻止默认行为，让浏览器跳转到新页面
        }
        
        // 如果是内部链接（以#开头），阻止默认行为并切换页面
        e.preventDefault();
        e.stopPropagation();
        console.log('  - 阻止默认行为，查找目标 section:', href);
        
        const target = document.querySelector(href);
        if (!target) {
          console.error('  - ❌ 找不到目标 section:', href);
          console.groupEnd();
          return;
        }
        
        console.log('  - ✅ 找到目标 section:', target.id);
        const success = window.switchToPage(href);
        if (!success) {
          console.error('  - ❌ 页面切换失败');
        } else {
          console.log('  - ✅ 页面切换成功');
        }
        console.groupEnd();
      };
      
      card.addEventListener('click', eventHandler, true); // 使用捕获阶段
      console.log('  - ✅ 已绑定addEventListener事件（捕获阶段）');
      
      // 添加鼠标悬停事件用于调试
      card.addEventListener('mouseenter', function() {
        console.log(`🖱️ 鼠标悬停在卡片 ${index} 上`);
      });
      
      card.addEventListener('mousedown', function(e) {
        console.log(`🖱️ 鼠标按下在卡片 ${index} 上`, e);
      });
      
      card.addEventListener('mouseup', function(e) {
        console.log(`🖱️ 鼠标释放在卡片 ${index} 上`, e);
      });
      
      console.log(`✅ 卡片 ${index} 绑定完成:`, href);
      console.groupEnd();
    });
    
    console.log('✅ 所有首页卡片点击事件已绑定');
    console.groupEnd();
  }
  
  // 只在首页绑定首页卡片点击事件
  if (window.location.pathname.endsWith('index.html') || window.location.pathname.endsWith('/')) {
    console.log('🚀 开始初始化首页卡片点击事件绑定...');
    bindHomeCards();
    
    // 延迟绑定，确保DOM完全加载
    setTimeout(() => {
      console.log('🔄 100ms后重新绑定首页卡片...');
      bindHomeCards();
    }, 100);
  } else {
    console.log('⏭️ 跳过首页卡片绑定（不在首页）');
  }
  
  // 添加全局诊断函数
  window.diagnoseHomeCards = function() {
    console.group('🔍 首页卡片诊断工具');
    console.log('开始诊断首页卡片点击问题...\n');
    
    const results = {
      homeSectionExists: false,
      cardsFound: false,
      cardsCount: 0,
      cardsWithHref: 0,
      cardsClickable: 0,
      issues: []
    };
    
    // 1. 检查home section
    console.log('1️⃣ 检查 #home section...');
    const homeSection = document.getElementById('home');
    if (homeSection) {
      console.log('✅ #home section 存在');
      results.homeSectionExists = true;
    } else {
      console.error('❌ #home section 不存在');
      results.issues.push('找不到 #home section');
    }
    console.log('');
    
    // 2. 检查卡片
    console.log('2️⃣ 检查 .home-feature-card 元素...');
    const cards = document.querySelectorAll('.home-feature-card');
    results.cardsCount = cards.length;
    console.log(`找到 ${cards.length} 个卡片`);
    
    if (cards.length === 0) {
      console.error('❌ 未找到任何卡片');
      results.issues.push('未找到任何 .home-feature-card 元素');
    } else {
      results.cardsFound = true;
      console.log('✅ 找到卡片');
    }
    console.log('');
    
    // 3. 检查每个卡片
    console.log('3️⃣ 检查每个卡片的详细信息...');
    cards.forEach((card, index) => {
      console.group(`卡片 ${index}`);
      const href = card.getAttribute('href');
      const computedStyle = window.getComputedStyle(card);
      
      console.log('  - href:', href || '❌ 无');
      if (href) results.cardsWithHref++;
      
      console.log('  - 可见性:', card.offsetWidth > 0 && card.offsetHeight > 0 ? '✅ 可见' : '❌ 不可见');
      console.log('  - pointer-events:', computedStyle.pointerEvents);
      console.log('  - z-index:', computedStyle.zIndex);
      console.log('  - position:', computedStyle.position);
      console.log('  - display:', computedStyle.display);
      console.log('  - visibility:', computedStyle.visibility);
      console.log('  - opacity:', computedStyle.opacity);
      console.log('  - onclick:', card.onclick ? '✅ 已设置' : '❌ 未设置');
      
      // 检查是否可点击
      const isClickable = computedStyle.pointerEvents !== 'none' && 
                         computedStyle.display !== 'none' && 
                         computedStyle.visibility !== 'hidden' &&
                         parseFloat(computedStyle.opacity) > 0;
      
      if (isClickable) {
        results.cardsClickable++;
        console.log('  - 可点击性: ✅ 可点击');
      } else {
        console.log('  - 可点击性: ❌ 不可点击');
        results.issues.push(`卡片 ${index} 不可点击（pointer-events: ${computedStyle.pointerEvents}, display: ${computedStyle.display}, visibility: ${computedStyle.visibility}, opacity: ${computedStyle.opacity}）`);
      }
      
      // 检查是否被覆盖
      const rect = card.getBoundingClientRect();
      const centerElement = document.elementFromPoint(
        rect.left + rect.width / 2,
        rect.top + rect.height / 2
      );
      if (centerElement !== card && !card.contains(centerElement)) {
        console.log('  - 覆盖检查: ⚠️ 可能被其他元素覆盖');
        console.log('  - 覆盖元素:', centerElement);
        results.issues.push(`卡片 ${index} 可能被元素覆盖: ${centerElement.tagName}.${centerElement.className}`);
      } else {
        console.log('  - 覆盖检查: ✅ 未被覆盖');
      }
      
      console.groupEnd();
    });
    console.log('');
    
    // 4. 生成报告
    console.log('📋 诊断报告:');
    console.log('='.repeat(50));
    console.log('home section 存在:', results.homeSectionExists ? '✅' : '❌');
    console.log('找到卡片:', results.cardsFound ? '✅' : '❌');
    console.log('卡片数量:', results.cardsCount);
    console.log('有href的卡片:', results.cardsWithHref);
    console.log('可点击的卡片:', results.cardsClickable);
    console.log('问题数量:', results.issues.length);
    console.log('='.repeat(50));
    
    if (results.issues.length > 0) {
      console.log('\n❌ 发现的问题:');
      results.issues.forEach((issue, index) => {
        console.log(`${index + 1}. ${issue}`);
      });
    } else {
      console.log('\n✅ 未发现明显问题');
    }
    
    console.groupEnd();
    return results;
  };
  
  console.log('💡 提示：在控制台运行 diagnoseHomeCards() 来诊断首页卡片问题');
}

// 图片生成功能
function initImageGeneration() {
  // 检查元素是否存在（在首页可能不存在）
  if (!elements.generateImageBtn || !elements.imagePrompt) {
    console.log('⏭️ 跳过图片生成初始化（元素不存在）');
    return;
  }
  
  // 启动时加载一次 LoRA 列表
  loadLoras().catch(err => {
    console.warn('加载 LoRA 列表失败（如果你没装 LoRA 插件可以忽略）：', err);
  });
  // 生成图片
  elements.generateImageBtn.addEventListener('click', async () => {
    const prompt = elements.imagePrompt.value.trim();
    if (!prompt) {
      alert('请输入图片描述');
      return;
    }

    const config = {
      prompt,
      negativePrompt: elements.imageNegativePrompt?.value.trim() || '',
      style: elements.imageStyle.value,
      size: elements.imageSize.value,
      count: parseInt(elements.imageCount.value) || 1,
      steps: parseInt(elements.imageSteps?.value) || 20
    };

    await generateImage(config);
  });

  // 清空输出
  elements.clearImageBtn.addEventListener('click', () => {
    elements.imageOutput.innerHTML = `
      <div class="empty-preview">
        <div class="preview-icon">🖼️</div>
        <p>生成的图片将显示在这里</p>
      </div>
    `;
  });

  // 下载全部
  elements.downloadAllBtn.addEventListener('click', () => {
    const images = elements.imageOutput.querySelectorAll('img');
    images.forEach((img, index) => {
      downloadImage(img.src, `image-${Date.now()}-${index}.png`);
    });
  });

  // 历史记录点击
  elements.imageHistory.addEventListener('click', (e) => {
    const item = e.target.closest('.history-item');
    if (item) {
      const prompt = item.dataset.prompt;
      elements.imagePrompt.value = prompt;
    }
  });
}

// 生成图片
async function generateImage(config) {
  try {
    elements.generateImageBtn.disabled = true;
    elements.imageLoading.classList.remove('hidden');
    
    // 模拟API调用（实际应用中需要替换为真实API）
    const images = await mockImageGeneration(config);
    
    // 显示结果
    displayImageResults(images);
    
    // 保存到历史
    saveToHistory(config.prompt);
    
  } catch (error) {
    console.error('生成图片失败:', error);
    
    // 更详细的错误提示
    let errorMessage = '生成图片失败';
    if (error.message.includes('fetch')) {
      errorMessage = '无法连接到 Stable Diffusion WebUI API\n\n请检查：\n1. WebUI 是否已启动并启用了 API 模式\n2. API 地址是否正确（在设置中配置）\n3. 两台设备是否在同一网络\n\n错误详情：' + error.message;
    } else if (error.message.includes('API请求失败')) {
      errorMessage = 'API 请求失败\n\n' + error.message + '\n\n请检查 WebUI 的运行状态';
    }
    
    alert(errorMessage);
  } finally {
    elements.generateImageBtn.disabled = false;
    elements.imageLoading.classList.add('hidden');
  }
}

// 调用 Stable Diffusion WebUI API 生成图片
async function mockImageGeneration(config) {
  const [width, height] = config.size.split('x');
  
  // 构建 prompt，添加风格信息
  let prompt = config.prompt;

  // 如果选择了 LoRA，则在最前面拼接 LoRA 标签
  if (elements.loraSelect && elements.loraSelect.value) {
    let loraName = elements.loraSelect.value.trim();
    
    // 确保 LoRA 名称格式正确（移除扩展名和特殊字符）
    loraName = loraName.replace(/\.(safetensors|ckpt|pt)$/i, '');
    loraName = loraName.replace(/[<>:]/g, ''); // 移除可能干扰的字符
    
    if (loraName) {
      let weight = 0.8;
      if (elements.loraWeight && elements.loraWeight.value) {
        const w = parseFloat(elements.loraWeight.value);
        if (!isNaN(w) && w > 0 && w <= 2) {
          weight = w;
        }
      }
      // 使用正确的 LoRA 格式：<lora:name:weight>
      prompt = `<lora:${loraName}:${weight}> ` + prompt;
      console.log(`✅ 已添加 LoRA: <lora:${loraName}:${weight}>`);
    }
  }
  const stylePrompts = {
    'realistic': 'realistic, photorealistic, high quality, detailed',
    'anime': 'anime style, manga style, japanese animation',
    'oil-painting': 'oil painting, classical art, masterpiece',
    'watercolor': 'watercolor painting, soft colors, artistic',
    'sketch': 'pencil sketch, line art, black and white',
    'cyberpunk': 'cyberpunk, futuristic, neon lights, sci-fi',
    'fantasy': 'fantasy art, magical, mystical, epic'
  };
  
  if (stylePrompts[config.style]) {
    prompt = `${prompt}, ${stylePrompts[config.style]}`;
  }
  
  // 构建负面提示词（使用用户输入的，如果没有则使用默认值）
  const defaultNegativePrompt = 'lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry';
  const negativePrompt = config.negativePrompt || defaultNegativePrompt;
  
  // 获取采样步数（用户设置的值，默认20）
  const steps = config.steps || 20;
  // 确保步数在合理范围内
  const validSteps = Math.max(1, Math.min(150, steps));
  
  // 构建 API 请求参数
  const requestBody = {
    prompt: prompt,
    negative_prompt: negativePrompt,
    steps: validSteps,
    cfg_scale: 7,
    width: parseInt(width),
    height: parseInt(height),
    sampler_index: 'DPM++ 2M Karras',
    batch_size: Math.min(config.count, 4), // WebUI 通常最多支持4张
    n_iter: 1
  };
  
  try {
    // 调用 Stable Diffusion WebUI API
    const response = await fetch(`${state.apiUrl}/sdapi/v1/txt2img`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API请求失败: ${response.status} ${response.statusText}\n${errorText}`);
    }
    
    const data = await response.json();
    
    // 将 base64 图片数据转换为 data URL
    const images = data.images.map(base64Image => {
      return `data:image/png;base64,${base64Image}`;
    });
    
    return images;
    
  } catch (error) {
    console.error('API调用错误:', error);
    throw error;
  }
}

// 从 WebUI 读取 LoRA 列表并填充下拉框
async function loadLoras() {
  if (!elements.loraSelect) {
    console.warn('loadLoras: LoRA 选择器不存在，跳过加载');
    return;
  }
  
  try {
    // 使用与图片生成相同的 API 地址来源，保证与设置面板保持一致
    const baseUrl = getApiBaseUrl();
    
    // 尝试多个可能的 API 端点
    const endpoints = [
      `${baseUrl.replace(/\/+$/, '')}/sdapi/v1/extra-networks/lora`,
      `${baseUrl.replace(/\/+$/, '')}/sdapi/v1/loras`,
      `${baseUrl.replace(/\/+$/, '')}/sdapi/v1/extra-networks`
    ];
    
    let data = null;
    let lastError = null;
    
    // 尝试每个端点
    for (const url of endpoints) {
      try {
        console.log('loadLoras: 正在从', url, '加载 LoRA 列表...');
        
        const res = await fetch(url, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        if (res.ok) {
          const responseData = await res.json();
          
          // 处理不同的响应格式
          if (Array.isArray(responseData)) {
            data = responseData;
          } else if (responseData.items && Array.isArray(responseData.items)) {
            data = responseData.items;
          } else if (responseData.loras && Array.isArray(responseData.loras)) {
            data = responseData.loras;
          } else {
            console.warn('loadLoras: 响应格式不符合预期:', responseData);
            continue;
          }
          
          if (data && data.length > 0) {
            console.log(`loadLoras: 成功从 ${url} 加载 ${data.length} 个 LoRA 模型`);
            break;
          }
        } else {
          console.warn(`loadLoras: ${url} 返回状态码 ${res.status}`);
        }
      } catch (fetchError) {
        console.warn(`loadLoras: ${url} 请求失败:`, fetchError.message);
        lastError = fetchError;
        continue;
      }
    }
    
    // 如果所有端点都失败
    if (!data) {
      throw new Error(`无法从任何端点加载 LoRA 列表。请确保 WebUI 已启动并启用了 API 模式。最后错误: ${lastError?.message || '未知错误'}`);
    }

    // 先保留第一个「不使用 LoRA」选项
    elements.loraSelect.innerHTML = '<option value="">不使用 LoRA</option>';

    data.forEach((lora) => {
      const opt = document.createElement('option');
      // 处理不同的数据格式
      // 格式1: {name, alias, ...}
      // 格式2: {name: "xxx", ...}
      // 格式3: 字符串数组
      let loraName = '';
      let loraAlias = '';
      
      if (typeof lora === 'string') {
        loraName = lora;
        loraAlias = lora;
      } else if (lora.name) {
        loraName = lora.name;
        loraAlias = lora.alias || lora.name;
      } else if (lora.title) {
        loraName = lora.title;
        loraAlias = lora.title;
      } else {
        console.warn('loadLoras: 无法解析 LoRA 数据:', lora);
        return;
      }
      
      // 移除文件扩展名（如果有）
      loraName = loraName.replace(/\.(safetensors|ckpt|pt)$/i, '');
      
      opt.value = loraName;
      opt.textContent = loraAlias || loraName;
      elements.loraSelect.appendChild(opt);
    });
    
    console.log('loadLoras: LoRA 列表已更新到下拉框');
  } catch (error) {
    // 所有错误都会被捕获并重新抛出，由调用者处理
    console.warn('loadLoras: 加载失败（如果你没装 LoRA 插件或 WebUI 未运行，可以忽略）:', error.message);
    throw error;
  }
}

// 显示图片结果
function displayImageResults(images) {
  if (images.length === 0) {
    elements.imageOutput.innerHTML = `
      <div class="empty-preview">
        <div class="preview-icon">🖼️</div>
        <p>未生成图片</p>
      </div>
    `;
    return;
  }

  elements.imageOutput.innerHTML = '';
  images.forEach((imageData, index) => {
    const imageContainer = document.createElement('div');
    imageContainer.className = 'image-result';
    
    // 转义单引号以防止 XSS
    const safeImageData = imageData.replace(/'/g, "\\'");
    
    imageContainer.innerHTML = `
      <img src="${safeImageData}" alt="生成的图片 ${index + 1}" loading="lazy">
      <div class="image-actions">
        <button onclick="downloadBase64Image('${safeImageData}', 'image-${Date.now()}-${index}.png')">下载</button>
        <button onclick="copyBase64Image('${safeImageData}')">复制图片</button>
      </div>
    `;
    elements.imageOutput.appendChild(imageContainer);
  });
}

// 保存到历史记录
function saveToHistory(prompt) {
  if (!prompt || state.imageHistory.includes(prompt)) return;
  
  state.imageHistory.unshift(prompt);
  if (state.imageHistory.length > 10) {
    state.imageHistory = state.imageHistory.slice(0, 10);
  }
  
  localStorage.setItem('imageHistory', JSON.stringify(state.imageHistory));
  updateHistoryDisplay();
}

// 更新历史记录显示
function updateHistoryDisplay() {
  if (!elements.imageHistory) {
    return; // 元素不存在，跳过（例如在首页）
  }
  
  if (state.imageHistory.length === 0) {
    elements.imageHistory.innerHTML = '<p class="empty-state">暂无生成记录</p>';
    return;
  }

  elements.imageHistory.innerHTML = state.imageHistory.map(prompt => `
    <div class="history-item" data-prompt="${prompt.replace(/"/g, '&quot;')}">
      <p>${prompt.length > 50 ? prompt.substring(0, 50) + '...' : prompt}</p>
    </div>
  `).join('');
}

// 音频克隆功能
function initVoiceClone() {
  // 如果页面使用独立的 Gradio Client 实现，跳过初始化
  if (window.__DISABLE_VOICE_CLONE_INIT__) {
    console.log('⏭️ 跳过 script.js 中的音频克隆初始化（页面使用独立的 Gradio Client 实现）');
    return;
  }
  
  if (!elements.voiceGenerateBtn) return;
  
  // 模式选择改变时，更新操作步骤
  if (elements.voiceMode) {
    // 初始化时加载默认模式的操作步骤
    loadInstruction(elements.voiceMode.value);
    
    // 监听模式改变
    elements.voiceMode.addEventListener('change', (e) => {
      const selectedMode = e.target.value;
      loadInstruction(selectedMode);
    });
  }
  
  // Prompt 音频上传预览和自动识别
  if (elements.voicePromptUpload) {
    elements.voicePromptUpload.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (file && file.type.startsWith('audio/')) {
        const url = URL.createObjectURL(file);
        if (elements.voicePromptPlayer) {
          elements.voicePromptPlayer.src = url;
        }
        if (elements.voicePromptPreview) {
          elements.voicePromptPreview.classList.remove('hidden');
        }
        
        // 显示识别按钮（API 端点存在，可以正常使用）
        if (elements.voiceRecognizeBtn) {
          elements.voiceRecognizeBtn.style.display = 'inline-block';
          elements.voiceRecognizeBtn.disabled = false; // 启用按钮
          elements.voiceRecognizeBtn.title = '点击识别音频中的 Prompt 文本';
          elements.voiceRecognizeBtn.dataset.file = 'upload'; // 标记文件来源
        }
      }
    });
  }
  
  // 录制音频文件处理
  if (elements.voicePromptRecord) {
    elements.voicePromptRecord.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (file && file.type.startsWith('audio/')) {
        // 显示识别按钮（API 端点存在，可以正常使用）
        if (elements.voiceRecognizeBtn) {
          elements.voiceRecognizeBtn.style.display = 'inline-block';
          elements.voiceRecognizeBtn.disabled = false; // 启用按钮
          elements.voiceRecognizeBtn.title = '点击识别音频中的 Prompt 文本';
          elements.voiceRecognizeBtn.dataset.file = 'record'; // 标记文件来源
        }
      }
    });
  }
  
  // 识别 Prompt 文本按钮
  if (elements.voiceRecognizeBtn) {
    elements.voiceRecognizeBtn.addEventListener('click', async () => {
      const fileSource = elements.voiceRecognizeBtn.dataset.file;
      let audioFile = null;
      
      if (fileSource === 'upload' && elements.voicePromptUpload) {
        audioFile = elements.voicePromptUpload.files[0];
      } else if (fileSource === 'record' && elements.voicePromptRecord) {
        audioFile = elements.voicePromptRecord.files[0];
      }
      
      if (!audioFile) {
        alert('请先上传或录制音频文件');
        return;
      }
      
      try {
        // 根据文件来源选择不同的 API 端点
        // upload 使用 /prompt_wav_recognition
        // record 使用 /prompt_wav_recognition_1
        const recognizedText = await recognizePromptWav(audioFile, fileSource);
        if (recognizedText && elements.voicePromptText) {
          elements.voicePromptText.value = recognizedText;
          console.log('✅ Prompt 文本已自动填充');
          // 显示成功提示
          if (elements.voiceRecognizeBtn) {
            const originalText = elements.voiceRecognizeBtn.innerHTML;
            elements.voiceRecognizeBtn.innerHTML = '<span class="btn-icon">✅</span> <span>识别成功</span>';
            setTimeout(() => {
              elements.voiceRecognizeBtn.innerHTML = originalText;
            }, 2000);
          }
        }
      } catch (error) {
        console.error('识别 Prompt 文本失败:', error);
        // 显示友好的错误提示
        const errorMsg = error.message.includes('暂时不可用') 
          ? '音频识别功能暂时不可用，请手动在"Prompt 文本"输入框中输入文本。'
          : '识别 Prompt 文本失败：' + error.message;
        alert(errorMsg);
      }
    });
  }
  
  // 生成随机种子（调用 API）
  if (elements.voiceGenerateSeed) {
    elements.voiceGenerateSeed.addEventListener('click', async () => {
      try {
        // 显示加载状态
        const originalText = elements.voiceGenerateSeed.innerHTML;
        elements.voiceGenerateSeed.disabled = true;
        elements.voiceGenerateSeed.innerHTML = '<span>生成中...</span>';
        
        // 调用 /generate_seed API
        const seed = await generateSeed();
        
        if (elements.voiceSeed) {
          elements.voiceSeed.value = seed;
          console.log('✅ 随机种子已生成:', seed);
        }
      } catch (error) {
        console.error('生成随机种子失败:', error);
        // 如果 API 失败，使用本地随机数作为降级方案
        const randomSeed = Math.floor(Math.random() * 1000000);
        if (elements.voiceSeed) {
          elements.voiceSeed.value = randomSeed;
        }
        alert('API 生成种子失败，已使用本地随机数');
      } finally {
        // 恢复按钮状态
        elements.voiceGenerateSeed.disabled = false;
        elements.voiceGenerateSeed.innerHTML = '随机生成';
      }
    });
  }
  
  // 生成音频
  elements.voiceGenerateBtn.addEventListener('click', async () => {
    const text = elements.voiceCloneText ? elements.voiceCloneText.value.trim() : '';
    if (!text) {
      alert('请输入要合成的文本');
      return;
    }
    
    const promptFile = elements.voicePromptUpload ? elements.voicePromptUpload.files[0] : null;
    const recordFile = elements.voicePromptRecord ? elements.voicePromptRecord.files[0] : null;
    
    if (!promptFile && !recordFile) {
      alert('请上传或录制 Prompt 音频文件');
      return;
    }
    
    try {
      await generateVoiceAudio({
        text: text,
        mode: elements.voiceMode ? elements.voiceMode.value : '3s极速复刻',
        promptText: elements.voicePromptText ? elements.voicePromptText.value.trim() : '',
        promptFile: promptFile || recordFile,
        instructText: elements.voiceInstructText ? elements.voiceInstructText.value.trim() : '',
        seed: elements.voiceSeed ? parseInt(elements.voiceSeed.value) || 0 : 0,
        stream: elements.voiceStream ? elements.voiceStream.checked : false
      });
    } catch (error) {
      console.error('生成音频失败:', error);
      alert('生成音频失败：' + error.message);
    }
  });
  
  // 清空结果
  if (elements.voiceClearBtn) {
    elements.voiceClearBtn.addEventListener('click', () => {
      if (elements.voiceOutput) {
        elements.voiceOutput.innerHTML = `
          <div class="empty-preview">
            <div class="preview-icon">🎵</div>
            <p>生成的音频将显示在这里</p>
          </div>
        `;
      }
      if (elements.voiceDownloadBtn) {
        elements.voiceDownloadBtn.style.display = 'none';
      }
    });
  }
}

// 测试 API 连接（调试用）
// 在浏览器控制台运行 testApiConnection() 来测试所有 API 端点
async function testApiConnection() {
  const COSYVOICE_API_URL = 'https://funaudiollm-fun-cosyvoice3-0-5b.ms.show';
  const testResults = [];
  
  console.log('🔍 开始测试 API 连接...');
  console.log('📝 注意：某些端点可能不存在，这是正常的');
  
  // 要测试的端点列表
  const endpoints = [
    { name: '基础 URL', url: '/', method: 'GET' },
    { name: '/api/', url: '/api/', method: 'GET' },
    { name: '/api/info', url: '/api/info', method: 'GET' },
    { name: '/api/generate_audio', url: '/api/generate_audio', method: 'POST', body: { data: [] } },
    { name: '/api/generate_seed', url: '/api/generate_seed', method: 'POST', body: { data: [] } },
    { name: '/api/change_instruction', url: '/api/change_instruction', method: 'POST', body: { data: ['3s极速复刻'] } },
    { name: '/api/prompt_wav_recognition', url: '/api/prompt_wav_recognition', method: 'POST', body: { data: [] } },
    { name: '/api/prompt_wav_recognition_1', url: '/api/prompt_wav_recognition_1', method: 'POST', body: { data: [] } },
  ];
  
  for (const endpoint of endpoints) {
    try {
      const options = {
        method: endpoint.method
      };
      
      if (endpoint.body) {
        options.headers = { 'Content-Type': 'application/json' };
        options.body = JSON.stringify(endpoint.body);
      }
      
      const response = await fetch(`${COSYVOICE_API_URL}${endpoint.url}`, options);
      const result = await response.json().catch(() => null);
      
      testResults.push({
        name: endpoint.name,
        url: `${COSYVOICE_API_URL}${endpoint.url}`,
        status: response.status,
        ok: response.ok,
        result: result
      });
      
      if (response.ok) {
        console.log(`✅ ${endpoint.name}:`, response.status, result);
      } else {
        console.warn(`⚠️ ${endpoint.name}:`, response.status, result);
      }
    } catch (error) {
      testResults.push({
        name: endpoint.name,
        url: `${COSYVOICE_API_URL}${endpoint.url}`,
        error: error.message
      });
      console.error(`❌ ${endpoint.name} 失败:`, error);
    }
  }
  
  console.log('📊 API 连接测试结果:', testResults);
  console.log('💡 提示：如果某个端点返回 404，说明该端点不存在或未暴露');
  return testResults;
}

// 调用 CosyVoice API 生成音频（使用 Fun-CosyVoice3-0.5B 创空间 API）
// 根据官方 Gradio 客户端示例: https://www.modelscope.cn/studios/FunAudioLLM/Fun-CosyVoice3-0.5B
async function generateVoiceAudio(config) {
  // 使用新的 Fun-CosyVoice3-0.5B 创空间 API
  // 创空间链接: https://www.modelscope.cn/studios/FunAudioLLM/Fun-CosyVoice3-0.5B
  const COSYVOICE_API_URL = 'https://funaudiollm-fun-cosyvoice3-0-5b.ms.show';
  
  try {
    if (elements.voiceLoading) elements.voiceLoading.classList.remove('hidden');
    if (elements.voiceGenerateBtn) {
      elements.voiceGenerateBtn.disabled = true;
      elements.voiceGenerateBtn.innerHTML = '<span class="btn-icon">⏳</span> <span>生成中...</span>';
    }
    
    // 检查是否有音频文件
    if (!config.promptFile) {
      throw new Error('请上传或录制 Prompt 音频文件');
    }
    
    console.log('🔍 使用 Fun-CosyVoice3-0.5B 创空间 API:', COSYVOICE_API_URL);
    console.log('🔍 参数配置:');
    console.log('  - tts_text:', config.text);
    console.log('  - mode_checkbox_group:', config.mode);
    console.log('  - prompt_text:', config.promptText || '');
    console.log('  - instruct_text:', config.instructText || '');
    console.log('  - seed:', config.seed);
    console.log('  - stream:', config.stream ? 'true' : 'false');
    
    // 根据官方 Gradio 客户端示例，直接使用 FormData 传递文件
    // 不需要先上传，直接在 API 调用中包含文件
    console.log('🔍 准备调用生成音频 API...');
    
    // 使用 FormData 构建请求，包含所有参数和文件
    const formData = new FormData();
    
    // 添加文本参数
    formData.append('data', JSON.stringify([
      config.text, // tts_text: string
      config.mode, // mode_checkbox_group: string
      config.promptText || '', // prompt_text: string
      null, // prompt_wav_upload: 文件将通过 files 字段传递
      null, // prompt_wav_record: 文件将通过 files 字段传递
      config.instructText || '', // instruct_text: string
      typeof config.seed === 'number' ? config.seed : parseInt(config.seed) || 0, // seed: number
      config.stream ? 'true' : 'false' // stream: string
    ]));
    
    // 添加音频文件（两个位置都需要相同的文件）
    formData.append('files', config.promptFile);
    formData.append('files', config.promptFile);
    
    // 构建请求数据（用于日志）
    const requestData = {
      data: [
        config.text,
        config.mode,
        config.promptText || '',
        '[File]',
        '[File]',
        config.instructText || '',
        typeof config.seed === 'number' ? config.seed : parseInt(config.seed) || 0,
        config.stream ? 'true' : 'false'
      ]
    };
    
    console.log('🔍 调用命名端点 /generate_audio');
    console.log('🔍 请求数据:', JSON.stringify(requestData, null, 2));
    
    // 使用 FormData 调用 API（包含文件）
    // 不设置 Content-Type，让浏览器自动设置 FormData 的边界
    // 注意：本地 Gradio 服务的 API 端点路径应该是 /generate_audio（没有 /api 前缀）
    const response = await fetch(`${COSYVOICE_API_URL}/generate_audio`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ API 调用失败:', response.status, errorText);
      throw new Error(`API 调用失败: ${response.status} ${errorText}`);
    }
    
    const result = await response.json();
    console.log('✅ API 调用成功，返回结果:', result);
    
    // 处理返回结果
    // Gradio 返回格式: { data: [...] }
    let audioUrl = null;
    
    if (result && result.data && result.data.length > 0) {
      const audioData = result.data[0];
      
      if (typeof audioData === 'string') {
        // 如果是字符串路径
        if (audioData.startsWith('http')) {
          audioUrl = audioData;
        } else {
          audioUrl = `${COSYVOICE_API_URL}/file=${encodeURIComponent(audioData)}`;
        }
      } else if (audioData && typeof audioData === 'object') {
        // 如果是对象，可能包含 path、url、name 等属性
        const filePath = audioData.path || audioData.url || audioData.name;
        if (filePath) {
          if (filePath.startsWith('http')) {
            audioUrl = filePath;
          } else {
            audioUrl = `${COSYVOICE_API_URL}/file=${encodeURIComponent(filePath)}`;
          }
        }
      }
    }
    
    if (!audioUrl) {
      console.error('❌ 无法解析返回的音频路径，返回数据:', result);
      throw new Error('无法解析返回的音频路径');
    }
    
    console.log('✅ 音频生成成功，URL:', audioUrl);
    
    // 显示结果
    if (elements.voiceOutput) {
      elements.voiceOutput.innerHTML = `
        <div class="audio-preview">
          <audio controls style="width: 100%;">
            <source src="${audioUrl}" type="audio/wav">
          </audio>
          <div style="margin-top: 1rem; display: flex; gap: 0.5rem;">
            <a href="${audioUrl}" download="generated_audio.wav" class="secondary-btn" style="text-decoration: none;">
              <span class="btn-icon">⬇️</span> 下载音频
            </a>
          </div>
        </div>
      `;
    }
    
    if (elements.voiceDownloadBtn) {
      elements.voiceDownloadBtn.href = audioUrl;
      elements.voiceDownloadBtn.download = 'generated_audio.wav';
      elements.voiceDownloadBtn.style.display = 'inline-block';
    }
    
  } catch (error) {
    console.error('生成音频失败:', error);
    if (elements.voiceOutput) {
      elements.voiceOutput.innerHTML = `
        <div class="error-message">
          <p>生成失败: ${error.message}</p>
        </div>
      `;
    }
    throw error;
  } finally {
    if (elements.voiceLoading) elements.voiceLoading.classList.add('hidden');
    if (elements.voiceGenerateBtn) {
      elements.voiceGenerateBtn.disabled = false;
      elements.voiceGenerateBtn.innerHTML = '<span class="btn-icon">🎤</span> <span>生成音频</span>';
    }
  }
}

// 调用 /change_instruction API 获取操作步骤
async function loadInstruction(mode) {
  const COSYVOICE_API_URL = 'https://funaudiollm-fun-cosyvoice3-0-5b.ms.show';
  
  if (!elements.voiceInstruction) return;
  
  // 根据模式显示默认操作步骤（API 端点可能不存在，直接使用默认提示）
  const defaultInstructions = {
    '3s极速复刻': '1. 上传或录制 Prompt 音频文件（采样率不低于16kHz）\n2. 输入要合成的文本\n3. 可选：填写 Prompt 文本和 Instruct 文本\n4. 点击"生成音频"按钮',
    '自然语言控制': '1. 上传或录制 Prompt 音频文件（采样率不低于16kHz）\n2. 输入要合成的文本\n3. 填写 Instruct 文本（用于控制语音风格和表达方式）\n4. 可选：填写 Prompt 文本\n5. 点击"生成音频"按钮'
  };
  
  // 直接显示默认操作步骤（API 端点可能不可用）
  if (elements.voiceInstruction) {
    elements.voiceInstruction.textContent = defaultInstructions[mode] || defaultInstructions['3s极速复刻'];
    return;
  }
  
  // 以下代码保留用于未来 API 可用时使用
  /*
  try {
    const response = await fetch(`${COSYVOICE_API_URL}/api/change_instruction`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ data: [mode] })
    });
    
    if (response.ok) {
      const result = await response.json();
      if (result && result.data && result.data.length > 0) {
        const instructionText = result.data[0];
        if (typeof instructionText === 'string') {
          elements.voiceInstruction.textContent = instructionText;
          return;
        }
      }
    }
  } catch (error) {
    console.warn('API 调用失败，使用默认提示:', error);
  }
  
  if (elements.voiceInstruction) {
    elements.voiceInstruction.textContent = defaultInstructions[mode] || defaultInstructions['3s极速复刻'];
  }
  */
}

// 调用 /generate_seed API 生成随机种子
// 注意：如果 API 端点不存在，将使用本地随机数生成
async function generateSeed() {
  const COSYVOICE_API_URL = 'https://funaudiollm-fun-cosyvoice3-0-5b.ms.show';
  
  // 先尝试调用 API，如果失败则使用本地随机数
  try {
    console.log('🔍 尝试调用 /generate_seed API');
    
    // 注意：本地 Gradio 服务的 API 端点路径应该是 /generate_seed（没有 /api 前缀）
    const response = await fetch(`${COSYVOICE_API_URL}/generate_seed`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ data: [] })
    });
    
    if (response.ok) {
      const result = await response.json();
      if (result && result.data && result.data.length > 0) {
        const seed = result.data[0];
        if (typeof seed === 'number') {
          console.log('✅ API 生成种子成功:', seed);
          return seed;
        } else {
          const parsedSeed = parseInt(seed);
          if (!isNaN(parsedSeed)) {
            console.log('✅ API 生成种子成功:', parsedSeed);
            return parsedSeed;
          }
        }
      }
    }
  } catch (error) {
    console.warn('API 调用失败，使用本地随机数生成:', error);
  }
  
  // 如果 API 失败，使用本地随机数生成（降级方案）
  const localSeed = Math.floor(Math.random() * 1000000);
  console.log('✅ 使用本地随机数生成:', localSeed);
  return localSeed;
}

// 调用 Prompt 音频识别 API 识别 Prompt 文本
// fileSource: 'upload' 使用 /prompt_wav_recognition，'record' 使用 /prompt_wav_recognition_1
async function recognizePromptWav(audioFile, fileSource = 'upload') {
  const COSYVOICE_API_URL = 'https://funaudiollm-fun-cosyvoice3-0-5b.ms.show';
  
  try {
    // 显示识别状态
    if (elements.voiceRecognizeBtn) {
      const originalText = elements.voiceRecognizeBtn.innerHTML;
      elements.voiceRecognizeBtn.disabled = true;
      elements.voiceRecognizeBtn.innerHTML = '<span class="btn-icon">⏳</span> <span>识别中...</span>';
    }
    
    // 根据文件来源选择不同的 API 端点名称
    // upload: /prompt_wav_recognition (用于上传的音频)
    // record: /prompt_wav_recognition_1 (用于录制的音频)
    const apiName = fileSource === 'record' 
      ? '/prompt_wav_recognition_1' 
      : '/prompt_wav_recognition';
    
    console.log(`🔍 调用 ${apiName} API，文件来源: ${fileSource}`);
    
    // 尝试多种调用方式
    let response = null;
    let result = null;
    let lastError = null;
    
    // 方式1: 直接使用命名端点路径（不带 /api/ 前缀）
    try {
      const formData = new FormData();
      formData.append('data', JSON.stringify([null])); // prompt_wav 位置用 null 占位
      formData.append('files', audioFile); // 文件通过 files 字段传递
      
      response = await fetch(`${COSYVOICE_API_URL}${apiName}`, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        result = await response.json();
        console.log(`✅ ${apiName} 成功（方式1）`);
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.warn('方式1失败，尝试方式2:', error);
      lastError = error;
      
      // 方式2: 使用 /api/ 前缀
      try {
        const formData = new FormData();
        formData.append('data', JSON.stringify([null]));
        formData.append('files', audioFile);
        
        response = await fetch(`${COSYVOICE_API_URL}/api${apiName}`, {
          method: 'POST',
          body: formData
        });
        
        if (response.ok) {
          result = await response.json();
          console.log(`✅ /api${apiName} 成功（方式2）`);
        } else {
          throw new Error(`HTTP ${response.status}`);
        }
      } catch (error2) {
        console.warn('方式2也失败，尝试方式3:', error2);
        lastError = error2;
        
        // 方式3: 使用 /run/ 路径（Gradio 的另一种 API 格式）
        try {
          const formData = new FormData();
          formData.append('data', JSON.stringify([null]));
          formData.append('files', audioFile);
          
          response = await fetch(`${COSYVOICE_API_URL}/run${apiName}`, {
            method: 'POST',
            body: formData
          });
          
          if (response.ok) {
            result = await response.json();
            console.log(`✅ /run${apiName} 成功（方式3）`);
          } else {
            throw new Error(`HTTP ${response.status}`);
          }
        } catch (error3) {
          console.warn('方式3也失败，尝试方式4:', error3);
          lastError = error3;
          
          // 方式4: 使用 /api/predict 并指定 api_name（FormData 格式）
          try {
            const formData = new FormData();
            formData.append('data', JSON.stringify([null]));
            formData.append('files', audioFile);
            formData.append('api_name', apiName);
            
            response = await fetch(`${COSYVOICE_API_URL}/api/predict`, {
              method: 'POST',
              body: formData
            });
            
            if (response.ok) {
              result = await response.json();
              console.log(`✅ /api/predict (${apiName}) 成功（方式4）`);
            } else {
              throw new Error(`HTTP ${response.status}`);
            }
          } catch (error4) {
            console.error('所有方式都失败:', error4);
            lastError = error4;
            throw new Error(`API 调用失败: ${lastError.message}。请手动在"Prompt 文本"输入框中输入文本。`);
          }
        }
      }
    }
    
    // 处理返回结果
    // API 返回格式: { data: [string] }，string 是识别出的 prompt 文本
    if (result && result.data && result.data.length > 0) {
      const recognizedText = result.data[0];
      if (typeof recognizedText === 'string' && recognizedText.trim()) {
        return recognizedText;
      } else {
        throw new Error('识别结果为空，请手动输入 Prompt 文本');
      }
    } else {
      throw new Error('API 返回数据为空，请手动输入 Prompt 文本');
    }
  } catch (error) {
    console.error('❌ 识别 Prompt 文本失败:', error);
    throw error;
  } finally {
    // 恢复按钮状态
    if (elements.voiceRecognizeBtn) {
      elements.voiceRecognizeBtn.disabled = false;
      elements.voiceRecognizeBtn.innerHTML = '<span class="btn-icon">🎯</span> <span>识别 Prompt 文本</span>';
    }
  }
}

// 处理音频 API 响应（已废弃，保留用于兼容性）
function handleVoiceResponse(result, apiUrl) {
  // 处理返回结果
  if (result.data && result.data.length > 0) {
    const audioPath = result.data[0];
    let audioUrl;
    
    // 处理文件路径
    if (typeof audioPath === 'string') {
      if (audioPath.startsWith('http')) {
        audioUrl = audioPath;
      } else {
        // Gradio 文件路径格式
        audioUrl = `${apiUrl}/file=${audioPath}`;
      }
    } else if (audioPath && audioPath.name) {
      audioUrl = `${apiUrl}/file=${audioPath.name}`;
    } else if (audioPath && typeof audioPath === 'object') {
      // 尝试其他可能的格式
      audioUrl = `${apiUrl}/file=${audioPath.path || audioPath.url || JSON.stringify(audioPath)}`;
    } else {
      throw new Error('无法解析返回的音频路径。返回数据: ' + JSON.stringify(result));
    }
    
    // 显示结果
    displayVoiceResult(audioUrl);
    
  } else {
    throw new Error('API 返回数据为空。完整响应: ' + JSON.stringify(result));
  }
}

// 显示音频生成结果
function displayVoiceResult(audioUrl) {
  if (!elements.voiceOutput) return;
  
  elements.voiceOutput.innerHTML = `
    <div class="audio-result">
      <audio controls style="width: 100%; margin: 1rem 0;">
        <source src="${audioUrl}" type="audio/wav">
        您的浏览器不支持音频播放。
      </audio>
      <div class="result-actions" style="margin-top: 1rem; display: flex; gap: 0.5rem;">
        <button onclick="downloadVoiceAudio('${audioUrl}')" class="secondary-btn">下载音频</button>
        <button onclick="copyVoiceUrl('${audioUrl}')" class="secondary-btn">复制链接</button>
      </div>
    </div>
  `;
  
  if (elements.voiceDownloadBtn) {
    elements.voiceDownloadBtn.style.display = 'inline-block';
    elements.voiceDownloadBtn.onclick = () => downloadVoiceAudio(audioUrl);
  }
}

// 下载音频
function downloadVoiceAudio(audioUrl) {
  const a = document.createElement('a');
  a.href = audioUrl;
  a.download = `cosyvoice-${Date.now()}.wav`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// 复制音频链接
function copyVoiceUrl(audioUrl) {
  navigator.clipboard.writeText(audioUrl).then(() => {
    alert('音频链接已复制到剪贴板');
  }).catch(err => {
    console.error('复制失败:', err);
    alert('复制失败');
  });
}

// 数字人生成功能
function initDigitalHuman() {
  // 检查元素是否存在（在首页可能不存在）
  if (!elements.modeTabs || elements.modeTabs.length === 0) {
    console.log('⏭️ 跳过数字人生成初始化（元素不存在）');
    return;
  }
  
  // 模式切换
  elements.modeTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const mode = tab.dataset.mode;
      state.currentMode = mode;
      
      elements.modeTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      
      if (mode === 'text') {
        elements.textMode.classList.add('active');
        elements.uploadMode.classList.remove('active');
      } else {
        elements.textMode.classList.remove('active');
        elements.uploadMode.classList.add('active');
      }
    });
  });

  // 图片上传
  elements.imageUploadArea.addEventListener('click', () => {
    elements.humanImageInput.click();
  });

  elements.imageUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.imageUploadArea.style.borderColor = 'rgba(255, 107, 129, 0.5)';
  });

  elements.imageUploadArea.addEventListener('dragleave', () => {
    elements.imageUploadArea.style.borderColor = 'rgba(255, 255, 255, 0.2)';
  });

  elements.imageUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.imageUploadArea.style.borderColor = 'rgba(255, 255, 255, 0.2)';
    
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      handleImageUpload(file);
    }
  });

  elements.humanImageInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      handleImageUpload(file);
    }
  });

  // 音频上传处理
  const audioInput = document.getElementById('audio-input');
  const audioPreview = document.getElementById('audio-preview');
  const audioPlayer = document.getElementById('audio-player');
  
  if (audioInput && audioPreview && audioPlayer) {
    audioInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file && file.type.startsWith('audio/')) {
        const url = URL.createObjectURL(file);
        audioPlayer.src = url;
        audioPreview.classList.remove('hidden');
      }
    });
  }

  // SadTalker 设置：同步滑块和数字输入框
  if (elements.poseStyle && elements.poseStyleValue) {
    elements.poseStyle.addEventListener('input', (e) => {
      elements.poseStyleValue.value = e.target.value;
    });
    elements.poseStyleValue.addEventListener('input', (e) => {
      const value = Math.max(0, Math.min(45, parseInt(e.target.value) || 0));
      elements.poseStyle.value = value;
      elements.poseStyleValue.value = value;
    });
  }

  if (elements.batchSize && elements.batchSizeValue) {
    elements.batchSize.addEventListener('input', (e) => {
      elements.batchSizeValue.value = e.target.value;
    });
    elements.batchSizeValue.addEventListener('input', (e) => {
      const value = Math.max(1, Math.min(8, parseInt(e.target.value) || 2));
      elements.batchSize.value = value;
      elements.batchSizeValue.value = value;
    });
  }

  // 生成数字人
  elements.generateHumanBtn.addEventListener('click', async () => {
    // 检查是否上传了图片
    const imageFile = elements.humanImageInput.files[0];
    if (!imageFile) {
      alert('请先上传人脸图片');
        return;
      }

    // 检查是否上传了音频
    const audioFile = audioInput ? audioInput.files[0] : null;
    if (!audioFile) {
      alert('请先上传驱动音频文件');
        return;
    }

    await generateDigitalHuman({
      imageFile: imageFile,
      audioFile: audioFile
    });
  });

  // 语音合成开关（如果元素存在）
  if (elements.enableVoice) {
  elements.enableVoice.addEventListener('change', (e) => {
    if (e.target.checked) {
        elements.voiceOptions && elements.voiceOptions.classList.remove('hidden');
    } else {
        elements.voiceOptions && elements.voiceOptions.classList.add('hidden');
    }
  });
  }

  // 生成语音（如果元素存在）
  if (elements.generateVoiceBtn) {
  elements.generateVoiceBtn.addEventListener('click', async () => {
      const text = elements.voiceText ? elements.voiceText.value.trim() : '';
    if (!text) {
      alert('请输入要合成的文本');
      return;
    }

      await generateVoice(text, elements.voiceType ? elements.voiceType.value : '');
  });
  }

  // 动画按钮
  elements.animateHumanBtn.addEventListener('click', () => {
    const humanImage = elements.humanOutput.querySelector('img');
    if (humanImage) {
      alert('动画功能开发中...');
    } else {
      alert('请先生成数字人');
    }
  });

  // 下载数字人
  elements.downloadHumanBtn.addEventListener('click', () => {
    const humanImage = elements.humanOutput.querySelector('img');
    if (humanImage) {
      downloadImage(humanImage.src, `digital-human-${Date.now()}.png`);
    } else {
      alert('请先生成数字人');
    }
  });
}

// 处理图片上传
function handleImageUpload(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    elements.uploadedPreview.src = e.target.result;
    elements.uploadedPreview.classList.remove('hidden');
    elements.imageUploadArea.querySelector('.upload-content').style.display = 'none';
  };
  reader.readAsDataURL(file);
}

// 文件转Base64
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

// 生成数字人
async function generateDigitalHuman(config) {
  try {
    elements.generateHumanBtn.disabled = true;
    elements.humanLoading.classList.remove('hidden');
    
    // 调用真实的 SadTalker API
    const videoUrl = await callSadTalkerAPI(config.imageFile, config.audioFile);
    console.log('generateDigitalHuman 获取到的 videoUrl:', videoUrl);
    
    if (!videoUrl) {
      throw new Error('视频生成成功，但未返回视频 URL');
    }
    
    // 显示结果
    displayHumanResult({ videoUrl, config });
    
    // 保存到图库
    saveToGallery({ videoUrl, config });
    
  } catch (error) {
    console.error('生成数字人失败:', error);
    
    // 更详细的错误提示
    let errorMessage = '生成数字人失败';
    if (error.message.includes('fetch')) {
      errorMessage = '无法连接到 SadTalker API\n\n请检查：\n1. WebUI 是否已启动并启用了 API 模式\n2. API 地址是否正确（在设置中配置）\n3. 是否已安装 SadTalker 扩展\n\n错误详情：' + error.message;
    } else {
      errorMessage = '生成失败：' + error.message + '\n\n提示：如果 data 数组参数不正确，请查看浏览器控制台的详细错误信息';
    }
    
    alert(errorMessage);
  } finally {
    elements.generateHumanBtn.disabled = false;
    elements.humanLoading.classList.add('hidden');
  }
}

// 上传文件到 Gradio（如果需要）
async function uploadFileToGradio(file, base, sessionHash) {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await fetch(`${base}/upload`, {
      method: 'POST',
      body: formData
    });
    
    if (response.ok) {
      const data = await response.json();
      // Gradio 返回格式可能是 { name: "文件名" } 或直接是文件路径
      return data.name || data;
    }
  } catch (error) {
    console.warn('文件上传失败，将使用 base64:', error);
  }
  
  // 如果上传失败，返回 base64
  return await fileToBase64(file);
}

// 获取 Gradio API 信息（找到正确的 fn_index）
async function getGradioAPIInfo(base) {
  try {
    const response = await fetch(`${base}/api/info`);
    if (response.ok) {
      const info = await response.json();
      console.log('Gradio API 信息:', info);
      return info;
    }
  } catch (error) {
    console.warn('无法获取 Gradio API 信息，使用默认 fn_index:', error);
  }
  return null;
}

// 通过 WebSocket 调用 SadTalker API 生成视频
async function callSadTalkerAPI(imageFile, audioFile) {
  const base = getApiBaseUrl();
  
  // 获取 session_hash（Gradio 需要）
  const sessionHash = generateSessionHash();
  
  // 使用正确的 fn_index（根据 WebSocket 消息中的实际值）
  // 注意：fn_index 可能每次 WebUI 启动时不同，需要根据实际情况调整
  let fnIndex = 857; // 根据 WebSocket 消息中的实际值（如果不行，可以尝试 931）
  try {
    const apiInfo = await getGradioAPIInfo(base);
    // 如果找到了 API 信息，可以尝试找到 SadTalker 的函数索引
    // 但通常直接使用 73 也可以
  } catch (error) {
    console.warn('使用默认 fn_index: 73');
  }
  
  // 验证文件类型
  if (!imageFile.type.startsWith('image/')) {
    throw new Error('图片文件格式不支持，请使用 JPG、PNG 等图片格式');
  }
  
  if (!audioFile.type.startsWith('audio/')) {
    throw new Error('音频文件格式不支持，请使用 WAV、MP3 等音频格式');
  }
  
  // Gradio 的音频和图片组件期望接收文件路径，而不是 base64
  // 需要先上传文件，获取文件路径
  console.log('上传文件到 Gradio...');
  
  let imageData, audioData;
  
  try {
    // 上传图片
    const imageFormData = new FormData();
    imageFormData.append('files', imageFile);
    const imageUploadResponse = await fetch(`${base}/upload`, {
      method: 'POST',
      body: imageFormData
    });
    
    if (imageUploadResponse.ok) {
      const imageUploadData = await imageUploadResponse.json();
      console.log('图片上传原始返回:', imageUploadData);
      
      // Gradio 返回格式可能是：
      // 1. 字符串路径: "C:\Users\..."
      // 2. 对象: {name: "路径"}
      // 3. 数组: [{name: "路径"}]
      // 4. 数组中的字符串: ["路径"]
      
      if (Array.isArray(imageUploadData) && imageUploadData.length > 0) {
        const firstItem = imageUploadData[0];
        if (typeof firstItem === 'string') {
          // 数组中的字符串
          imageData = { name: firstItem, is_file: true };
        } else if (typeof firstItem === 'object' && firstItem !== null) {
          // 数组中的对象
          imageData = firstItem;
          if (!imageData.is_file) {
            imageData.is_file = true;
          }
        }
      } else if (imageUploadData && typeof imageUploadData === 'object' && imageUploadData.name) {
        // 直接是对象
        imageData = imageUploadData;
        if (!imageData.is_file) {
          imageData.is_file = true;
        }
      } else if (typeof imageUploadData === 'string') {
        // 直接是字符串
        imageData = { name: imageUploadData, is_file: true };
      }
      console.log('图片上传成功，处理后数据:', imageData);
    } else {
      throw new Error('图片上传失败');
    }
    
    // 上传音频
    const audioFormData = new FormData();
    audioFormData.append('files', audioFile);
    const audioUploadResponse = await fetch(`${base}/upload`, {
      method: 'POST',
      body: audioFormData
    });
    
    if (audioUploadResponse.ok) {
      const audioUploadData = await audioUploadResponse.json();
      console.log('音频上传原始返回:', audioUploadData);
      
      // Gradio 返回格式可能是：
      // 1. 字符串路径: "C:\Users\..."
      // 2. 对象: {name: "路径"}
      // 3. 数组: [{name: "路径"}]
      // 4. 数组中的字符串: ["路径"]
      
      if (Array.isArray(audioUploadData) && audioUploadData.length > 0) {
        const firstItem = audioUploadData[0];
        if (typeof firstItem === 'string') {
          // 数组中的字符串
          audioData = { name: firstItem, is_file: true };
        } else if (typeof firstItem === 'object' && firstItem !== null) {
          // 数组中的对象
          audioData = firstItem;
          if (!audioData.is_file) {
            audioData.is_file = true;
          }
        }
      } else if (audioUploadData && typeof audioUploadData === 'object' && audioUploadData.name) {
        // 直接是对象
        audioData = audioUploadData;
        if (!audioData.is_file) {
          audioData.is_file = true;
        }
      } else if (typeof audioUploadData === 'string') {
        // 直接是字符串
        audioData = { name: audioUploadData, is_file: true };
      }
      console.log('音频上传成功，处理后数据:', audioData);
    } else {
      throw new Error('音频上传失败');
    }
    
  } catch (uploadError) {
    console.error('文件上传失败:', uploadError);
    // 如果上传失败，尝试使用 base64（虽然可能不工作，但至少可以尝试）
    console.warn('文件上传失败，尝试使用 base64 格式...');
    const imageBase64 = await fileToBase64(imageFile);
    const audioBase64 = await fileToBase64(audioFile);
    imageData = imageBase64;
    audioData = audioBase64;
  }
  
  // 根据原始 WebUI 的实际参数格式：
  // data[0]: "data:image/png;base64,..." - 图片是 base64 字符串
  // data[1]: {data: "data:audio/wav;base64,...", name: "audio.wav"} - 音频是对象格式
  // 需要将文件转换为 base64 格式
  
  // 转换图片为 base64
  if (typeof imageData === 'object' && imageData !== null && imageData.name) {
    // 如果已经是对象（从上传返回的），需要读取文件并转换为 base64
    console.log('图片数据是对象，需要转换为 base64');
    imageData = await fileToBase64(imageFile);
  } else if (typeof imageData === 'string' && !imageData.startsWith('data:')) {
    // 如果是文件路径，需要读取文件并转换为 base64
    console.log('图片数据是路径，需要转换为 base64');
    imageData = await fileToBase64(imageFile);
  } else if (typeof imageData === 'string' && imageData.startsWith('data:')) {
    // 已经是 base64 格式
    console.log('图片数据已经是 base64 格式');
  } else {
    // 默认转换为 base64
    imageData = await fileToBase64(imageFile);
  }
  
  // 转换音频为 base64 对象格式
  let audioBase64;
  if (typeof audioData === 'object' && audioData !== null && audioData.name) {
    // 如果已经是对象（从上传返回的），需要读取文件并转换为 base64
    console.log('音频数据是对象，需要转换为 base64');
    audioBase64 = await fileToBase64(audioFile);
  } else if (typeof audioData === 'string' && !audioData.startsWith('data:')) {
    // 如果是文件路径，需要读取文件并转换为 base64
    console.log('音频数据是路径，需要转换为 base64');
    audioBase64 = await fileToBase64(audioFile);
  } else if (typeof audioData === 'string' && audioData.startsWith('data:')) {
    // 已经是 base64 格式
    audioBase64 = audioData;
  } else {
    // 默认转换为 base64
    audioBase64 = await fileToBase64(audioFile);
  }
  
  // 音频格式：{data: "data:audio/wav;base64,...", name: "audio.wav"}
  audioData = {
    data: audioBase64.startsWith('data:') ? audioBase64 : `data:audio/wav;base64,${audioBase64}`,
    name: audioFile.name || 'audio.wav'
  };
  
  console.log('文件信息:', {
    imageType: imageFile.type,
    imageSize: imageFile.size,
    audioType: audioFile.type,
    audioSize: audioFile.size,
    imageData: imageData,
    audioData: audioData
  });
  
  // 读取 SadTalker 设置
  const poseStyle = elements.poseStyle ? parseInt(elements.poseStyle.value) || 0 : 0;
  const faceResolution = elements.faceResolution ? 
    Array.from(elements.faceResolution).find(r => r.checked)?.value || '256' : '256';
  const preprocess = elements.preprocess ? elements.preprocess.value || 'crop' : 'crop';
  const stillMode = elements.stillMode ? elements.stillMode.checked : false;
  const batchSize = elements.batchSize ? parseInt(elements.batchSize.value) || 2 : 2;
  const gfpganEnhancer = elements.gfpganEnhancer ? elements.gfpganEnhancer.checked : false;
  
  console.log('SadTalker 设置:', {
    poseStyle,
    faceResolution,
    preprocess,
    stillMode,
    batchSize,
    gfpganEnhancer
  });
  
  // 构建请求体
  // 根据原始 WebUI 的实际参数格式：
  // data[0]: "data:image/png;base64,..." - 图片 base64 字符串
  // data[1]: {data: "data:audio/wav;base64,...", name: "audio.wav"} - 音频对象
  // data[2]: preprocess - "crop"/"resize"/"full"/"extcrop"/"extfull"
  // data[3]: still - false (是否静态模式)
  // data[4]: 可能是其他布尔值或参数
  // data[5]: batch_size - 数字 (批量大小)
  // data[6]: face model resolution - 256 或 512
  // data[7]: pose_style - 0-45 (姿态风格)
  const requestBody = {
    data: [
      imageData,        // 0: 人脸图片（base64 字符串: "data:image/png;base64,..."）
      audioData,        // 1: 驱动音频（对象: {data: "data:audio/wav;base64,...", name: "audio.wav"}）
      preprocess,        // 2: preprocess (预处理方式: "crop"/"resize"/"full"/"extcrop"/"extfull")
      stillMode,        // 3: still (是否静态模式)
      false,            // 4: 可能是其他参数（根据原始 WebUI 的格式）
      batchSize,        // 5: batch_size (批量大小)
      parseInt(faceResolution), // 6: face model resolution (256 或 512)
      poseStyle         // 7: pose_style (0-45，姿态风格)
    ],
    event_data: null,
    fn_index: fnIndex,
    session_hash: sessionHash
  };

  // 调试：输出请求体（不输出完整的 base64，只输出长度）
  console.log('SadTalker API 请求:', {
    ...requestBody,
    data: requestBody.data.map((item, idx) => {
      if (typeof item === 'string' && item.length > 100) {
        return `[string, length: ${item.length}, preview: ${item.substring(0, 50)}...]`;
      } else if (typeof item === 'object' && item !== null) {
        // 输出文件对象的详细信息
        return `[object, keys: ${Object.keys(item).join(', ')}, name: ${item.name || 'N/A'}]`;
      } else if (typeof item === 'string' && item.length < 200) {
        // 输出短字符串（可能是文件路径）
        return `[string: ${item}]`;
      }
      return item;
    })
  });
  
  // 特别输出前两个参数（图片和音频）的详细信息
  console.log('图片数据:', {
    type: typeof requestBody.data[0],
    value: requestBody.data[0],
    length: typeof requestBody.data[0] === 'string' ? requestBody.data[0].length : 'N/A'
  });
  console.log('音频数据:', {
    type: typeof requestBody.data[1],
    value: requestBody.data[1],
    length: typeof requestBody.data[1] === 'string' ? requestBody.data[1].length : 'N/A'
  });

  try {
    // 方法1：先尝试使用 HTTP POST（同步方式，如果支持）
    console.log('尝试使用 HTTP POST 方式...');
    
    try {
      const response = await fetch(`${base}/run/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`HTTP POST 失败: ${response.status}`);
      }

      let data = await response.json();
      console.log('HTTP POST 返回数据:', data);
      
      // 如果 is_generating 为 true，需要轮询
      if (data.is_generating) {
        console.log('视频正在生成中，开始轮询...');
        
        // 轮询获取结果（最多等待 5 分钟）
        const maxAttempts = 60; // 60 次 * 5 秒 = 5 分钟
        let attempts = 0;
        
        while (attempts < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, 5000)); // 等待 5 秒
          
          const pollResponse = await fetch(`${base}/run/predict`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              data: [],
              event_data: null,
              fn_index: fnIndex,
              session_hash: sessionHash
            })
          });
          
          if (!pollResponse.ok) {
            throw new Error(`轮询失败: ${pollResponse.status}`);
          }
          
          data = await pollResponse.json();
          console.log(`轮询第 ${attempts + 1} 次，is_generating: ${data.is_generating}`);
          
          if (!data.is_generating && data.data && data.data.length > 0) {
            break; // 生成完成，退出循环
          }
          
          attempts++;
        }
        
        if (data.is_generating) {
          throw new Error('视频生成超时，请稍后重试');
        }
      }
      
      // 查找视频数据
      if (data.data && Array.isArray(data.data) && data.data.length > 0) {
        for (let i = 0; i < data.data.length; i++) {
          const item = data.data[i];
          if (Array.isArray(item) && item.length > 0) {
            const firstItem = item[0];
            if (firstItem && typeof firstItem === 'object' && firstItem.name) {
              let filePath = firstItem.name;
              console.log('提取的文件路径:', filePath);
              
              // Gradio 需要完整的文件路径，而不是只有文件名
              // 如果是 Windows 绝对路径，转换为 Gradio 可访问的格式
              if (filePath.includes('\\')) {
                // Windows 路径，尝试转换为相对路径
                // 尝试找到 outputs 目录后的路径
                const outputsIndex = filePath.indexOf('outputs');
                if (outputsIndex !== -1) {
                  // 使用 outputs 目录后的相对路径
                  filePath = filePath.substring(outputsIndex).replace(/\\/g, '/');
                } else {
                  // 如果是临时文件，需要保留完整路径
                  // Gradio 的临时文件需要通过完整路径访问
                  // 将反斜杠转换为正斜杠
                  filePath = filePath.replace(/\\/g, '/');
                }
              }
              
              // Gradio 的文件访问格式：/file=路径
              // 对于临时文件，可能需要完整路径
              const videoUrl = `${base}/file=${encodeURIComponent(filePath)}`;
              console.log('找到视频文件:', filePath, 'URL:', videoUrl);
              console.log('callSadTalkerAPI 返回 videoUrl:', videoUrl);
              return videoUrl;
            } else if (typeof firstItem === 'string') {
              // 如果是字符串，可能是文件路径或 URL
              console.log('提取的字符串路径:', firstItem);
              if (firstItem.startsWith('/file/') || firstItem.startsWith('file=')) {
                return `${base}${firstItem.startsWith('/') ? '' : '/'}${firstItem}`;
              } else if (firstItem.startsWith('data:video/')) {
                return firstItem;
              } else if (firstItem.includes('\\') || firstItem.includes('/')) {
                // 如果是文件路径，提取文件名
                const fileName = firstItem.split(/[\\/]/).pop();
                return `${base}/file=${encodeURIComponent(fileName)}`;
              } else {
                // 如果已经是文件名，直接使用
                return `${base}/file=${encodeURIComponent(firstItem)}`;
              }
            }
          }
        }
      }
      
      // 如果 HTTP POST 返回空数组，说明可能不支持同步方式，尝试 WebSocket
      if (data.data && data.data.length === 0) {
        console.log('HTTP POST 返回空数组，尝试 WebSocket...');
        throw new Error('HTTP_POST_EMPTY'); // 触发 WebSocket 尝试
      }
      
      throw new Error('HTTP POST 返回的数据格式不正确');
      
    } catch (httpError) {
      if (httpError.message === 'HTTP_POST_EMPTY') {
        // 继续尝试 WebSocket
        console.log('HTTP POST 返回空数组，尝试 WebSocket...');
      } else {
        console.warn('HTTP POST 失败，尝试 WebSocket:', httpError);
      }
      
      // 方法2：使用 WebSocket 连接（如果 HTTP 不可用）
      return await new Promise((resolve, reject) => {
        // 将 base URL 转换为 WebSocket URL
        // Gradio 的标准 WebSocket 端点是 /queue/join
        let wsUrl = base.replace(/^http(s?):\/\//, 'ws$1://');
        if (!wsUrl.endsWith('/queue/join')) {
          wsUrl = wsUrl + '/queue/join';
        }
        
        console.log('连接 WebSocket:', wsUrl);
        const ws = new WebSocket(wsUrl);
      
      let resolved = false;
      const timeout = setTimeout(() => {
        if (!resolved) {
          resolved = true;
          ws.close();
          reject(new Error('WebSocket 连接超时'));
        }
      }, 300000); // 5 分钟超时
      
      ws.onopen = () => {
        console.log('WebSocket 连接已建立，URL:', wsUrl);
        // 发送 session_hash 和 fn_index（Gradio 需要）
        const hashMessage = { 
          msg: 'send_hash', 
          session_hash: sessionHash,
          fn_index: fnIndex  // 添加 fn_index
        };
        console.log('发送 send_hash 消息:', hashMessage);
        ws.send(JSON.stringify(hashMessage));
      };
      
      let state = 'waiting_hash'; // 状态机：waiting_hash -> waiting_estimation -> waiting_send_data -> processing
      let actualFnIndex = fnIndex; // 使用服务器返回的 fn_index
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('WebSocket 消息:', message, '当前状态:', state);
          
          // 检查是否是 fn_index 和 session_hash 的响应（没有 msg 字段）
          if (!message.msg && message.fn_index !== undefined && message.session_hash) {
            // 收到服务器返回的 fn_index 和 session_hash
            actualFnIndex = message.fn_index; // 使用服务器返回的 fn_index
            console.log('收到服务器确认，fn_index:', actualFnIndex, 'session_hash:', message.session_hash);
            state = 'waiting_estimation';
            // 不需要发送任何东西，等待 estimation 消息
          } else if (message.msg === 'send_hash') {
            // 服务器发送的 send_hash 确认消息，可以忽略或记录
            console.log('收到 send_hash 确认消息');
            // 继续等待 fn_index 和 session_hash 的响应
          } else if (message.msg === 'estimation') {
            // 队列估计信息
            console.log('队列位置:', message.rank, '队列大小:', message.queue_size);
            state = 'waiting_send_data';
          } else if (message.msg === 'send_data') {
            // 收到发送数据请求，发送实际的请求数据
            console.log('收到 send_data 请求，发送数据... (fn_index:', actualFnIndex, ')');
            console.log('发送的完整 data 数组:', JSON.stringify(requestBody.data, null, 2));
            console.log('data[0] (图片):', typeof requestBody.data[0], requestBody.data[0]);
            console.log('data[1] (音频):', typeof requestBody.data[1], requestBody.data[1]);
            state = 'processing';
            ws.send(JSON.stringify({
              data: requestBody.data,
              event_data: null,
              fn_index: actualFnIndex, // 使用服务器返回的 fn_index
              session_hash: sessionHash
            }));
          } else if (message.msg === 'process_starts') {
            // 处理开始
            console.log('视频生成开始...');
          } else if (message.msg === 'process_completed') {
            // 处理完成，提取视频数据
            state = 'completed';
            clearTimeout(timeout);
            resolved = true;
            ws.close();
            
            // 检查是否成功
            if (message.success === false) {
              const errorMsg = message.error || message.message || '处理失败，但没有错误信息';
              console.error('处理失败:', errorMsg, '完整消息:', message);
              reject(new Error(`SadTalker 处理失败: ${errorMsg}`));
              return;
            }
            
            if (message.output && message.output.data) {
              const outputData = message.output.data;
              console.log('处理完成，输出数据:', JSON.stringify(outputData, null, 2));
              
              // 查找视频文件路径
              // outputData 格式通常是 [[{name: "文件路径"}, null], ...]
              // 或者 [[{name: "文件路径"}], ...]
              for (let i = 0; i < outputData.length; i++) {
                const item = outputData[i];
                if (Array.isArray(item) && item.length > 0) {
                  // 遍历数组中的每个元素，跳过 null
                  for (let j = 0; j < item.length; j++) {
                    const subItem = item[j];
                    if (subItem && typeof subItem === 'object' && subItem.name) {
                      // 找到文件路径（可能是 Windows 路径，如 C:\Users\...）
                      let filePath = subItem.name;
                      console.log('找到文件路径:', filePath);
                      
                      // Gradio 需要完整的文件路径，而不是只有文件名
                      // 如果是 Windows 绝对路径，转换为 Gradio 可访问的格式
                      if (filePath.includes('\\')) {
                        // Windows 路径，尝试转换为相对路径
                        // 尝试找到 outputs 目录后的路径
                        const outputsIndex = filePath.indexOf('outputs');
                        if (outputsIndex !== -1) {
                          // 使用 outputs 目录后的相对路径
                          filePath = filePath.substring(outputsIndex).replace(/\\/g, '/');
                        } else {
                          // 如果是临时文件，需要保留完整路径
                          // Gradio 的临时文件需要通过完整路径访问
                          // 将反斜杠转换为正斜杠
                          filePath = filePath.replace(/\\/g, '/');
                        }
                      }
                      
                      // 转换为 URL（Gradio 的文件访问格式）
                      // Gradio 使用 file=路径 格式
                      // 对于临时文件，使用完整路径
                      const videoUrl = `${base}/file=${encodeURIComponent(filePath)}`;
                      console.log('视频文件 URL:', videoUrl);
                      console.log('WebSocket 路径返回 videoUrl:', videoUrl);
                      resolve(videoUrl);
                      return;
                    } else if (subItem && typeof subItem === 'string') {
                      // 可能是 base64 或文件路径
                      if (subItem.startsWith('/file/') || subItem.startsWith('file=')) {
                        resolve(`${base}${subItem.startsWith('/') ? '' : '/'}${subItem}`);
                        return;
                      } else if (subItem.startsWith('data:video/')) {
                        resolve(subItem);
                        return;
                      } else if (subItem.length > 100 && !subItem.includes('\\') && !subItem.includes('/')) {
                        // 可能是 base64 视频数据
                        if (!subItem.startsWith('data:')) {
                          resolve(`data:video/mp4;base64,${subItem}`);
                          return;
                        }
                        resolve(subItem);
                        return;
                      }
                    }
                  }
                } else if (typeof item === 'string') {
                  // 直接是字符串路径
                  if (item.startsWith('/file/') || item.startsWith('file=')) {
                    resolve(`${base}${item.startsWith('/') ? '' : '/'}${item}`);
                    return;
                  } else if (item.startsWith('data:video/')) {
                    resolve(item);
                    return;
                  }
                }
              }
              
              // 输出详细的调试信息
              console.error('无法从输出数据中找到视频文件，输出数据:', JSON.stringify(outputData, null, 2));
              reject(new Error('无法从输出数据中找到视频文件。输出数据格式: ' + JSON.stringify(outputData).substring(0, 500)));
            } else {
              // 输出完整的消息用于调试
              console.error('处理完成但没有输出数据，完整消息:', JSON.stringify(message, null, 2));
              reject(new Error('处理完成但没有输出数据。消息内容: ' + JSON.stringify(message).substring(0, 500)));
            }
          } else if (message.msg === 'process_generating') {
            // 正在生成中
            console.log('正在生成视频...');
          } else if (message.msg === 'queue_full') {
            clearTimeout(timeout);
            resolved = true;
            ws.close();
            reject(new Error('队列已满，请稍后重试'));
          } else if (message.msg === 'error') {
            clearTimeout(timeout);
            resolved = true;
            ws.close();
            reject(new Error('处理出错: ' + (message.message || JSON.stringify(message))));
          }
        } catch (error) {
          console.error('解析 WebSocket 消息失败:', error);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket 错误:', error);
        clearTimeout(timeout);
        if (!resolved) {
          resolved = true;
          reject(new Error('WebSocket 连接错误: ' + (error.message || error)));
        }
      };
      
      ws.onclose = (event) => {
        console.log('WebSocket 连接关闭，代码:', event.code, '原因:', event.reason || '无', '当前状态:', state);
        clearTimeout(timeout);
        if (!resolved) {
          resolved = true;
          // 错误代码 1006 通常表示连接异常关闭
          if (event.code === 1006) {
            reject(new Error(
              `WebSocket 连接异常关闭 (代码: 1006)。\n\n` +
              `可能的原因：\n` +
              `1. WebUI 不支持 WebSocket 连接\n` +
              `2. 网络问题或防火墙阻止\n` +
              `3. WebSocket URL 不正确\n\n` +
              `当前状态: ${state}\n` +
              `WebSocket URL: ${wsUrl}\n\n` +
              `建议：\n` +
              `- 检查 WebUI 是否正常运行\n` +
              `- 尝试在浏览器中直接访问 WebUI 页面，确认 WebSocket 连接正常\n` +
              `- 检查浏览器控制台是否有其他错误信息`
            ));
          } else if (state !== 'processing' && state !== 'completed') {
            reject(new Error(`WebSocket 连接已关闭 (代码: ${event.code}, 原因: ${event.reason || '无'})。当前状态: ${state}`));
          }
        }
      };
      });
    }
  } catch (error) {
    console.error('SadTalker API 调用错误:', error);
    throw error;
  }
}

// 生成 session_hash（Gradio 需要）
function generateSessionHash() {
  // 生成一个随机字符串，类似 Gradio 的 session_hash
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

// 显示数字人结果（视频）
function displayHumanResult(result) {
  const videoUrl = result.videoUrl || result.imageUrl;
  console.log('displayHumanResult 接收到的数据:', result);
  console.log('videoUrl:', videoUrl);
  
  if (!videoUrl) {
    console.error('videoUrl 为空，无法显示视频');
  elements.humanOutput.innerHTML = `
      <div class="error-message">
        <p>视频生成成功，但无法获取视频 URL</p>
        <p>请检查浏览器控制台的详细日志</p>
      </div>
    `;
    return;
  }
  
  // 确保 videoUrl 是完整的 URL
  let finalVideoUrl = videoUrl;
  if (!videoUrl.startsWith('http://') && !videoUrl.startsWith('https://') && !videoUrl.startsWith('data:')) {
    // 如果不是完整 URL，添加 base URL
    const base = getApiBaseUrl();
    finalVideoUrl = videoUrl.startsWith('/') ? `${base}${videoUrl}` : `${base}/${videoUrl}`;
    console.log('修正后的 videoUrl:', finalVideoUrl);
  }
  
  // 使用更安全的方式创建视频元素，避免字符串转义问题
  elements.humanOutput.innerHTML = `
    <div class="video-result">
      <video id="human-video-player" controls style="width: 100%; max-width: 512px; border-radius: 8px;">
        <source src="" type="video/mp4">
        您的浏览器不支持视频播放
      </video>
      <div class="image-actions" style="margin-top: 1rem;">
        <button id="download-video-btn">下载视频</button>
        <button id="copy-video-url-btn">复制链接</button>
      </div>
    </div>
  `;
  
  // 设置视频源
  const videoElement = elements.humanOutput.querySelector('#human-video-player');
  const sourceElement = videoElement.querySelector('source');
  if (videoElement && sourceElement) {
    sourceElement.src = finalVideoUrl;
    videoElement.load(); // 重新加载视频
    console.log('视频源已设置:', finalVideoUrl);
  }
  
  // 设置按钮事件
  const downloadBtn = elements.humanOutput.querySelector('#download-video-btn');
  const copyBtn = elements.humanOutput.querySelector('#copy-video-url-btn');
  
  if (downloadBtn) {
    downloadBtn.addEventListener('click', () => {
      downloadVideo(finalVideoUrl, `sadtalker-${Date.now()}.mp4`);
    });
  }
  
  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      copyVideoUrl(finalVideoUrl);
    });
  }
  
  console.log('视频元素已创建，URL:', finalVideoUrl);
}

// 保存到图库
function saveToGallery(result) {
  const item = {
    imageUrl: result.imageUrl,
    timestamp: Date.now(),
    config: result.config
  };
  
  state.humanGallery.unshift(item);
  if (state.humanGallery.length > 20) {
    state.humanGallery = state.humanGallery.slice(0, 20);
  }
  
  localStorage.setItem('humanGallery', JSON.stringify(state.humanGallery));
  updateGalleryDisplay();
}

// 更新图库显示
function updateGalleryDisplay() {
  if (!elements.humanGallery) {
    return; // 元素不存在，跳过（例如在首页）
  }
  
  if (state.humanGallery.length === 0) {
    elements.humanGallery.innerHTML = '<p class="empty-state">暂无创建的数字人</p>';
    return;
  }

  elements.humanGallery.innerHTML = state.humanGallery.map((item, index) => `
    <div class="human-item" onclick="selectHumanFromGallery('${item.imageUrl}')">
      <img src="${item.imageUrl}" alt="数字人 ${index + 1}" loading="lazy">
    </div>
  `).join('');
}

// 从图库选择数字人
function selectHumanFromGallery(imageUrl) {
  elements.humanOutput.innerHTML = `
    <div class="image-result">
      <img src="${imageUrl}" alt="数字人" loading="lazy">
      <div class="image-actions">
        <button onclick="downloadImage('${imageUrl}', 'digital-human-${Date.now()}.png')">下载</button>
        <button onclick="copyImageUrl('${imageUrl}')">复制链接</button>
      </div>
    </div>
  `;
}

// 生成语音
async function generateVoice(text, voiceType) {
  try {
    elements.generateVoiceBtn.disabled = true;
    elements.generateVoiceBtn.textContent = '生成中...';
    
    // 模拟API调用（实际应用中需要替换为真实API）
    await mockVoiceGeneration(text, voiceType);
    
    alert('语音生成成功！');
  } catch (error) {
    console.error('生成语音失败:', error);
    alert('生成语音失败，请稍后重试');
  } finally {
    elements.generateVoiceBtn.disabled = false;
    elements.generateVoiceBtn.innerHTML = '<span class="btn-icon">🎤</span> 生成语音';
  }
}

// 模拟语音生成（实际应用中需要调用真实API）
async function mockVoiceGeneration(text, voiceType) {
  await new Promise(resolve => setTimeout(resolve, 2000));
  // 实际应用中应该返回音频文件URL
  console.log('生成语音:', text, voiceType);
}

// 设置功能
function initSettings() {
  // 加载设置
  elements.apiUrlInput.value = state.apiUrl;
  elements.defaultQuality.value = localStorage.getItem('defaultQuality') || 'standard';
  if (elements.deepseekApiKeyInput) {
    elements.deepseekApiKeyInput.value = state.deepseekApiKey;
  }
  if (elements.klingAccessKeyInput) {
    elements.klingAccessKeyInput.value = state.klingAccessKey;
  }
  if (elements.klingSecretKeyInput) {
    elements.klingSecretKeyInput.value = state.klingSecretKey;
  }
  
  // 设置输入框提示
  elements.apiUrlInput.placeholder = '例如: http://192.168.1.100:7860';

  // 打开设置
  elements.settingsBtn.addEventListener('click', () => {
    elements.settingsModal.showModal();
  });

  // 关闭设置
  elements.closeSettings.addEventListener('click', () => {
    elements.settingsModal.close();
  });

  elements.cancelSettings.addEventListener('click', () => {
    elements.settingsModal.close();
  });

  // 保存设置
  elements.saveSettings.addEventListener('click', () => {
    state.apiUrl = elements.apiUrlInput.value.trim();
    if (elements.deepseekApiKeyInput) {
      state.deepseekApiKey = elements.deepseekApiKeyInput.value.trim();
      localStorage.setItem('deepseekApiKey', state.deepseekApiKey);
    }
    if (elements.klingAccessKeyInput) {
      state.klingAccessKey = elements.klingAccessKeyInput.value.trim();
      localStorage.setItem('klingAccessKey', state.klingAccessKey);
    }
    if (elements.klingSecretKeyInput) {
      state.klingSecretKey = elements.klingSecretKeyInput.value.trim();
      localStorage.setItem('klingSecretKey', state.klingSecretKey);
    }
    localStorage.setItem('apiUrl', state.apiUrl);
    localStorage.setItem('defaultQuality', elements.defaultQuality.value);
    elements.settingsModal.close();
    alert('设置已保存');
  });

  // ========== AI 聊天功能 ==========
  if (elements.chatSidebar && elements.chatToggleBtn) {
    console.log('✅ 初始化 AI 聊天功能...');
    
    // 侧边栏展开/收起
    elements.chatToggleBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      console.log('🖱️ AI 助手按钮被点击');
      elements.chatSidebar.classList.toggle('expanded');
      console.log('📂 侧边栏状态:', elements.chatSidebar.classList.contains('expanded') ? '展开' : '收起');
    });

    if (elements.chatCloseBtn) {
      elements.chatCloseBtn.addEventListener('click', () => {
        elements.chatSidebar.classList.remove('expanded');
      });
    }

    // 清空对话
    if (elements.chatClearBtn) {
      elements.chatClearBtn.addEventListener('click', () => {
        if (confirm('确定要清空所有对话吗？')) {
          clearChatMessages();
        }
      });
    }

    // 标签切换
    if (elements.chatTabs) {
      elements.chatTabs.forEach(tab => {
        tab.addEventListener('click', () => {
          elements.chatTabs.forEach(t => t.classList.remove('active'));
          tab.classList.add('active');
          const tabType = tab.dataset.tab;
          updateChatPlaceholder(tabType);
        });
      });
    }

    // 快速操作按钮
    if (elements.quickActionBtns) {
      elements.quickActionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          const action = btn.dataset.action;
          handleQuickAction(action);
        });
      });
    }

    // 发送消息
    if (elements.chatSendBtn && elements.chatInput) {
      elements.chatSendBtn.addEventListener('click', sendChatMessage);
      elements.chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendChatMessage();
        }
      });
    }
    
    console.log('✅ AI 聊天功能初始化完成');
  } else {
    console.warn('⚠️ AI 聊天功能初始化失败：找不到必要元素');
    console.log('  - chatSidebar:', elements.chatSidebar ? '✅' : '❌');
    console.log('  - chatToggleBtn:', elements.chatToggleBtn ? '✅' : '❌');
  }
}

// 加载历史记录
function loadHistory() {
  updateHistoryDisplay();
}

// 加载图库
function loadGallery() {
  updateGalleryDisplay();
}

// 工具函数
function downloadImage(url, filename) {
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// 下载 base64 图片
function downloadBase64Image(base64Data, filename) {
  const link = document.createElement('a');
  link.href = base64Data;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// 复制 base64 图片到剪贴板
async function copyBase64Image(base64Data) {
  try {
    // 将 base64 转换为 blob
    const response = await fetch(base64Data);
    const blob = await response.blob();
    
    // 复制到剪贴板
    await navigator.clipboard.write([
      new ClipboardItem({
        [blob.type]: blob
      })
    ]);
    
    alert('图片已复制到剪贴板');
  } catch (err) {
    console.error('复制失败:', err);
    alert('复制失败，请使用下载功能');
  }
}

function copyImageUrl(url) {
  navigator.clipboard.writeText(url).then(() => {
    alert('链接已复制到剪贴板');
  }).catch(err => {
    console.error('复制失败:', err);
    alert('复制失败');
  });
}

// 下载视频
function downloadVideo(url, filename) {
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// 复制视频链接
function copyVideoUrl(url) {
  navigator.clipboard.writeText(url).then(() => {
    alert('视频链接已复制到剪贴板');
  }).catch(err => {
    console.error('复制失败:', err);
    alert('复制失败');
  });
}

// 全局函数（供HTML中的onclick调用）
window.downloadImage = downloadImage;
window.downloadBase64Image = downloadBase64Image;
window.copyBase64Image = copyBase64Image;
window.copyImageUrl = copyImageUrl;
window.selectHumanFromGallery = selectHumanFromGallery;
window.downloadVideo = downloadVideo;
window.copyVideoUrl = copyVideoUrl;

// ========== AI 聊天功能 ==========

// 清空聊天消息
function clearChatMessages() {
  if (elements.chatMessages) {
    elements.chatMessages.innerHTML = `
      <div class="chat-welcome">
        <div class="welcome-icon">🤖</div>
        <p>你好！我是 AI 助手</p>
        <p class="welcome-hint">我可以帮你：</p>
        <ul class="welcome-features">
          <li>📝 生成创意剧本</li>
          <li>✨ 生成 AI 提示词</li>
          <li>💡 提供创作建议</li>
        </ul>
      </div>
    `;
  }
}

// 更新聊天输入框占位符
function updateChatPlaceholder(tabType) {
  if (!elements.chatInput) return;
  
  const placeholders = {
    script: '输入你的需求，例如：生成一个关于未来科技的短剧本...',
    prompt: '描述你想要的图片或视频，例如：一个美丽的日落场景，海边，温暖的光线...'
  };
  
  elements.chatInput.placeholder = placeholders[tabType] || placeholders.script;
}

// 处理快速操作
function handleQuickAction(action) {
  if (!elements.chatInput) return;
  
  const prompts = {
    'script-short': '请生成一个3-5分钟的短剧本，主题自选，要求有完整的故事结构、人物对话和场景描述。',
    'script-long': '请生成一个20-30分钟的长剧本，主题自选，要求有完整的三幕结构、丰富的人物关系和详细的情节发展。',
    'prompt-image': '请为 Stable Diffusion 生成一个详细的图片提示词，描述一个美丽的场景，包括风格、色彩、构图等细节。',
    'prompt-video': '请为视频生成创建一个详细的提示词，描述一个动态场景，包括动作、镜头运动、氛围等。'
  };
  
  const prompt = prompts[action];
  if (prompt) {
    elements.chatInput.value = prompt;
    elements.chatInput.focus();
    // 自动发送
    setTimeout(() => sendChatMessage(), 100);
  }
}

// 添加聊天消息到界面
function addChatMessage(role, content, isStreaming = false) {
  if (!elements.chatMessages) return;
  
  // 移除欢迎消息
  const welcome = elements.chatMessages.querySelector('.chat-welcome');
  if (welcome) {
    welcome.remove();
  }
  
  const messageDiv = document.createElement('div');
  messageDiv.className = `chat-message ${role === 'user' ? 'user-message' : 'ai-message'}`;
  
  if (isStreaming) {
    messageDiv.classList.add('streaming');
  }
  
  messageDiv.innerHTML = `
    <div class="message-avatar">${role === 'user' ? '👤' : '🤖'}</div>
    <div class="message-content">
      <div class="message-text">${content}</div>
      ${role === 'ai' ? '<div class="message-actions"><button class="copy-message-btn" onclick="copyMessage(this)">复制</button></div>' : ''}
    </div>
  `;
  
  elements.chatMessages.appendChild(messageDiv);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  
  return messageDiv;
}

// 更新流式消息
function updateStreamingMessage(messageDiv, content) {
  if (messageDiv) {
    const textElement = messageDiv.querySelector('.message-text');
    if (textElement) {
      textElement.textContent = content;
      elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    }
  }
}

// 发送聊天消息
async function sendChatMessage() {
  if (!elements.chatInput || !elements.chatSendBtn) return;
  
  const message = elements.chatInput.value.trim();
  if (!message) return;
  
  // 获取当前标签类型
  const activeTab = document.querySelector('.chat-tab.active');
  const tabType = activeTab ? activeTab.dataset.tab : 'script';
  
  // 添加用户消息
  addChatMessage('user', message);
  
  // 清空输入框
  elements.chatInput.value = '';
  elements.chatInput.style.height = 'auto';
  
  // 禁用发送按钮
  elements.chatSendBtn.disabled = true;
  elements.chatSendBtn.textContent = '发送中...';
  
  // 添加AI消息占位符
  const aiMessageDiv = addChatMessage('ai', '正在思考...', true);
  
  try {
    // 调用AI API
    const response = await callAIChatAPI(message, tabType);
    
    // 更新AI消息
    updateStreamingMessage(aiMessageDiv, response);
    aiMessageDiv.classList.remove('streaming');
    
  } catch (error) {
    console.error('AI 聊天错误:', error);
    updateStreamingMessage(aiMessageDiv, `抱歉，发生了错误：${error.message}`);
    aiMessageDiv.classList.remove('streaming');
  } finally {
    // 恢复发送按钮
    elements.chatSendBtn.disabled = false;
    elements.chatSendBtn.innerHTML = '<span>发送</span>';
  }
}

// 调用AI聊天API
async function callAIChatAPI(message, tabType) {
  // 检查是否配置了 DeepSeek API Key
  if (!state.deepseekApiKey || state.deepseekApiKey.trim() === '') {
    throw new Error('请先在设置中配置 DeepSeek API Key');
  }
  
  // 根据标签类型构建不同的提示词
  let systemPrompt = '';
  let userPrompt = message;
  
  if (tabType === 'script') {
    // 剧本生成：只生成剧本内容，不要其他说明
    systemPrompt = `你是一个专业的剧本创作助手。你的任务是**只生成剧本内容**，不要添加任何解释、说明或其他文字。

要求：
1. 直接输出剧本内容，包括场景描述、人物对话、动作提示等
2. 使用标准的剧本格式（场景标题、人物名称、对话内容等）
3. 不要添加"以下是剧本"、"剧本如下"等前缀
4. 不要添加任何解释性文字、说明或建议
5. 只输出纯粹的剧本内容

格式示例：
【场景一】
时间：...
地点：...
人物：...

（场景描述）

人物A：（对话内容）

人物B：（对话内容）`;
  } else if (tabType === 'prompt') {
    // 提示词生成：只生成提示词，不要其他说明
    systemPrompt = `你是一个专业的AI提示词生成助手。你的任务是**只生成Stable Diffusion提示词**，不要添加任何解释、说明或其他文字。

要求：
1. 直接输出英文提示词（prompt），使用逗号分隔关键词
2. 可以包含负面提示词（negative prompt），用"Negative:"标记
3. 不要添加"以下是提示词"、"提示词如下"等前缀
4. 不要添加任何解释性文字、说明或建议
5. 只输出纯粹的提示词内容

格式示例：
masterpiece, best quality, highly detailed, 8k, professional photography, [具体描述], [风格], [构图], [色彩]

Negative: lowres, bad anatomy, bad hands, text, error, missing fingers`;
  }
  
  try {
    // 调用 DeepSeek API
    const response = await fetch('https://api.deepseek.com/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.deepseekApiKey}`
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt }
        ],
        stream: false,
        temperature: 0.7,
        max_tokens: 2000
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: { message: '未知错误' } }));
      throw new Error(errorData.error?.message || `API 请求失败: ${response.status}`);
    }
    
    const data = await response.json();
    
    // 提取回复内容
    if (data.choices && data.choices.length > 0 && data.choices[0].message) {
      return data.choices[0].message.content;
    } else {
      throw new Error('API 返回格式不正确');
    }
    
  } catch (error) {
    console.error('DeepSeek API 调用失败:', error);
    if (error.message.includes('API Key')) {
      throw new Error('DeepSeek API Key 无效，请检查设置中的配置');
    } else if (error.message.includes('网络') || error.message.includes('fetch')) {
      throw new Error('无法连接到 DeepSeek API，请检查网络连接');
    } else {
      throw error;
    }
  }
}

// 模拟AI响应（实际使用时需要替换为真实的API调用）
async function simulateAIResponse(message, tabType, systemPrompt) {
  // 模拟网络延迟
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // 根据标签类型生成不同的响应
  if (tabType === 'script') {
    return `【剧本标题】${message.includes('未来') ? '未来世界' : '创意故事'}

【场景一】
时间：现代/未来
地点：${message.includes('科技') ? '科技实验室' : '城市街道'}
人物：主角A、配角B

（场景描述）
${message.includes('短') ? '这是一个紧凑的场景，展现了主要冲突。' : '这是一个展开的场景，详细描述了环境和氛围。'}

主角A：（对话内容）
"${message}"

【场景二】
...

（注：这是一个示例剧本框架，实际使用时需要连接到真实的AI服务来生成完整内容。）`;
  } else if (tabType === 'prompt') {
    return `**English Prompt:**
${message}, masterpiece, best quality, highly detailed, 8k, professional photography, cinematic lighting, beautiful composition

**Negative Prompt:**
lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry

**Parameters:**
- Steps: 30
- CFG Scale: 7
- Sampler: DPM++ 2M Karras
- Size: 1024x1024

（注：这是一个示例提示词，实际使用时需要连接到真实的AI服务来生成更详细和个性化的提示词。）`;
  }
  
  return `我理解你的需求：${message}\n\n（注：这是一个模拟响应。要使用真实的AI功能，请配置 OpenAI API、Claude API 或其他AI服务。）`;
}

// ========== 图生视频功能 ==========

// ========== 图生视频功能（重写版本）==========

// 初始化图生视频功能
function initImageToVideo() {
  // 检查元素是否存在（在非图生视频页面可能不存在）
  if (!elements.videoImageInput || !elements.videoImageUploadArea) {
    return;
  }
  
  console.log('✅ 初始化图生视频功能...');

  // 图片上传区域点击事件
  elements.videoImageUploadArea.addEventListener('click', () => {
    if (elements.videoImageInput) {
      elements.videoImageInput.click();
    }
  });

  // 拖拽上传
  elements.videoImageUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.videoImageUploadArea.style.borderColor = 'var(--accent-gold)';
  });

  elements.videoImageUploadArea.addEventListener('dragleave', () => {
    elements.videoImageUploadArea.style.borderColor = 'var(--card-border)';
  });

  elements.videoImageUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.videoImageUploadArea.style.borderColor = 'var(--card-border)';
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type.startsWith('image/')) {
      handleVideoImageUpload(files[0]);
    }
  });

  // 文件选择器变化事件
  elements.videoImageInput.addEventListener('change', (e) => {
    const file = e.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      handleVideoImageUpload(file);
    }
  });

  // 滑块同步
  if (elements.videoDuration && elements.videoDurationValue) {
    elements.videoDuration.addEventListener('input', (e) => {
      elements.videoDurationValue.value = e.target.value;
    });
    elements.videoDurationValue.addEventListener('input', (e) => {
      const value = Math.max(1, Math.min(10, parseFloat(e.target.value) || 3));
      elements.videoDuration.value = value;
      elements.videoDurationValue.value = value;
    });
  }

  if (elements.videoStrength && elements.videoStrengthValue) {
    elements.videoStrength.addEventListener('input', (e) => {
      elements.videoStrengthValue.value = e.target.value;
    });
    elements.videoStrengthValue.addEventListener('input', (e) => {
      const value = Math.max(0.1, Math.min(1.0, parseFloat(e.target.value) || 0.5));
      elements.videoStrength.value = value;
      elements.videoStrengthValue.value = value;
    });
  }

  // 生成视频按钮
  if (elements.generateVideoBtn) {
    elements.generateVideoBtn.addEventListener('click', handleGenerateVideo);
  }
}

// 处理图片上传
function handleVideoImageUpload(file) {
  // 验证文件类型
  if (!file.type.startsWith('image/')) {
    alert('请上传图片文件（JPG、PNG等）');
    return;
  }

  // 获取预览元素（如果不存在则重新查找）
  const preview = elements.videoUploadedPreview || document.getElementById('video-uploaded-preview');
  if (!preview) {
    alert('图片预览元素未找到，请刷新页面重试');
    return;
  }

  // 读取图片文件
  const reader = new FileReader();
  reader.onload = (e) => {
    // 设置图片源
    preview.src = e.target.result;
    
    // 显示预览图片
    preview.classList.remove('hidden');
    preview.style.display = 'block';
    
    // 隐藏上传提示内容
    const uploadContent = elements.videoImageUploadArea?.querySelector('.upload-content');
    if (uploadContent) {
      uploadContent.style.display = 'none';
    }
    
    // 更新 elements 对象
    if (!elements.videoUploadedPreview) {
      elements.videoUploadedPreview = preview;
    }
    
    console.log('✅ 图片预览已显示');
  };
  
  reader.onerror = () => {
    alert('图片读取失败，请重试');
  };
  
  reader.readAsDataURL(file);
}

// 生成视频
async function handleGenerateVideo() {
  // 检查是否已上传图片
  const imageFile = elements.videoImageInput?.files?.[0];
  if (!imageFile) {
    alert('请先上传一张图片');
    return;
  }

  // 获取配置参数
  const config = {
    imageFile: imageFile,
    animationType: elements.videoAnimationType?.value || 'zoom-in',
    duration: parseFloat(elements.videoDuration?.value || 3),
    fps: parseInt(elements.videoFps?.value || 30),
    resolution: elements.videoResolution?.value || '768x768',
    strength: parseFloat(elements.videoStrength?.value || 0.5),
    prompt: elements.videoPrompt?.value.trim() || '',
    negativePrompt: elements.videoNegativePrompt?.value.trim() || '',
    loop: elements.videoLoop?.checked || false
  };

  // 显示加载状态
  if (elements.videoLoading) {
    elements.videoLoading.classList.remove('hidden');
  }
  if (elements.videoOutput) {
    elements.videoOutput.innerHTML = '';
  }
  if (elements.generateVideoBtn) {
    elements.generateVideoBtn.disabled = true;
    elements.generateVideoBtn.innerHTML = '<span class="btn-icon">⏳</span> <span>生成中...</span>';
  }

  try {
    // 调用图生视频API
    const videoUrl = await callImageToVideoAPI(config);

    // 显示生成的视频
    if (elements.videoOutput) {
      elements.videoOutput.innerHTML = `
        <video controls autoplay loop style="width: 100%; max-width: 100%; border-radius: 8px;">
          <source src="${videoUrl}" type="video/mp4">
          您的浏览器不支持视频播放
        </video>
        <div style="margin-top: 1rem; display: flex; gap: 1rem;">
          <a href="${videoUrl}" download="generated-video.mp4" class="secondary-btn" style="text-decoration: none; display: inline-flex; align-items: center; gap: 0.5rem;">
            <span>📥</span>
            <span>下载视频</span>
          </a>
        </div>
      `;
    }
  } catch (error) {
    console.error('生成视频失败:', error);
    if (elements.videoOutput) {
      elements.videoOutput.innerHTML = `
        <div class="empty-preview" style="color: var(--accent);">
          <div class="preview-icon">❌</div>
          <p>生成失败: ${error.message}</p>
        </div>
      `;
    }
    alert(`生成视频失败: ${error.message}`);
  } finally {
    // 恢复按钮状态
    if (elements.videoLoading) {
      elements.videoLoading.classList.add('hidden');
    }
    if (elements.generateVideoBtn) {
      elements.generateVideoBtn.disabled = false;
      elements.generateVideoBtn.innerHTML = '<span class="btn-icon">🎬</span> <span>生成视频</span>';
    }
  }
}

// 调用图生视频API
async function callImageToVideoAPI(config) {
  // 优先使用可灵API（如果已配置API Key）
  if (state.klingAccessKey && state.klingAccessKey.trim() !== '' && 
      state.klingSecretKey && state.klingSecretKey.trim() !== '') {
    try {
      return await callKlingAPI(config);
    } catch (error) {
      console.error('可灵API调用失败，尝试备用方案:', error);
      // 如果可灵API失败，继续尝试其他方法
    }
  } else {
    console.warn('未配置可灵API Key，使用备用方案');
  }

  // 备用方案：使用本地Stable Diffusion WebUI（如果支持）
  const base = getApiBaseUrl();
  
  // 将图片转换为base64
  const imageBase64 = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = reader.result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(config.imageFile);
  });

  // 解析分辨率
  const [width, height] = config.resolution.split('x').map(Number);

  // 构建提示词（根据动画类型）
  let animationPrompt = '';
  switch (config.animationType) {
    case 'zoom-in':
      animationPrompt = 'zoom in, smooth camera movement, cinematic';
      break;
    case 'zoom-out':
      animationPrompt = 'zoom out, smooth camera movement, cinematic';
      break;
    case 'pan-left':
      animationPrompt = 'pan left, smooth camera movement, cinematic';
      break;
    case 'pan-right':
      animationPrompt = 'pan right, smooth camera movement, cinematic';
      break;
    case 'pan-up':
      animationPrompt = 'pan up, smooth camera movement, cinematic';
      break;
    case 'pan-down':
      animationPrompt = 'pan down, smooth camera movement, cinematic';
      break;
    case 'rotate':
      animationPrompt = 'rotate, smooth camera movement, cinematic';
      break;
    case 'ken-burns':
      animationPrompt = 'ken burns effect, slow zoom, smooth movement, cinematic';
      break;
    case 'fade':
      animationPrompt = 'fade in, fade out, smooth transition, cinematic';
      break;
    default:
      animationPrompt = 'smooth camera movement, cinematic';
  }

  const fullPrompt = config.prompt 
    ? `${config.prompt}, ${animationPrompt}`
    : animationPrompt;

  // 使用 img2img API 作为基础，然后通过扩展生成视频
  // 注意：这需要后端支持 AnimateDiff 或其他视频生成扩展
  try {
    // 方法1：尝试使用 AnimateDiff 扩展（如果已安装）
    const response = await fetch(`${base}/sdapi/v1/img2img`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        init_images: [imageBase64],
        prompt: fullPrompt,
        negative_prompt: config.negativePrompt || 'blurry, distorted, low quality, bad animation',
        width: width,
        height: height,
        steps: 20,
        cfg_scale: 7,
        denoising_strength: config.strength,
        batch_size: 1,
        // AnimateDiff 相关参数（如果扩展支持）
        alwayson_scripts: {
          'AnimateDiff': {
            args: [
              true, // enable
              config.duration, // video_length
              config.fps, // fps
              config.loop // loop
            ]
          }
        }
      })
    });

    if (!response.ok) {
      throw new Error(`API 请求失败: ${response.status}`);
    }

    const data = await response.json();
    
    // 如果返回的是视频，直接使用
    if (data.video && data.video.length > 0) {
      return `data:video/mp4;base64,${data.video[0]}`;
    }
    
    // 如果返回的是图片序列，需要转换为视频（这里简化处理，实际可能需要后端支持）
    if (data.images && data.images.length > 0) {
      // 如果后端不支持直接生成视频，使用第一张图片作为占位
      // 实际应用中，应该将图片序列发送到后端进行视频合成
      throw new Error('后端暂不支持视频生成，请安装 AnimateDiff 扩展或使用可灵API');
    }

    throw new Error('API 返回数据格式不正确');
  } catch (error) {
    console.error('图生视频API调用失败:', error);
    throw new Error(`视频生成失败: ${error.message}。请确保已配置可灵API Key或安装AnimateDiff扩展。`);
  }
}

// 生成 JWT Token（使用 HS256 算法）
// 根据测试结果，可灵 API 需要使用 JWT Token 进行认证
// 算法：HS256
// 密钥格式：使用 Secret Key 作为签名密钥
async function generateKlingJWTToken(accessKey, secretKey) {
  // JWT Header: {"alg":"HS256","typ":"JWT"}
  const header = {
    alg: 'HS256',
    typ: 'JWT'
  };
  
  // JWT Payload: 包含 iss (issuer) 等信息
  // 根据测试结果，iss 应该是 Access Key
  const payload = {
    iss: accessKey,
    iat: Math.floor(Date.now() / 1000), // 当前时间戳（秒）
    exp: Math.floor(Date.now() / 1000) + 3600 // 过期时间（1小时后）
  };
  
  // Base64 URL 编码（先 JSON.stringify，再 Base64 编码）
  function base64UrlEncode(obj) {
    const json = JSON.stringify(obj);
    const base64 = btoa(unescape(encodeURIComponent(json)));
    return base64
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  }
  
  // 创建签名输入
  const encodedHeader = base64UrlEncode(header);
  const encodedPayload = base64UrlEncode(payload);
  const signatureInput = `${encodedHeader}.${encodedPayload}`;
  
  // 使用 Web Crypto API 生成 HMAC-SHA256 签名
  const encoder = new TextEncoder();
  const keyData = encoder.encode(secretKey);
  const messageData = encoder.encode(signatureInput);
  
  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  
  const signature = await crypto.subtle.sign('HMAC', cryptoKey, messageData);
  
  // 将签名转换为 Base64 URL
  const signatureArray = new Uint8Array(signature);
  let binaryString = '';
  for (let i = 0; i < signatureArray.length; i++) {
    binaryString += String.fromCharCode(signatureArray[i]);
  }
  const signatureBase64 = btoa(binaryString)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
  
  // 组合 JWT Token
  const token = `${signatureInput}.${signatureBase64}`;
  
  console.log('🔐 JWT Token 生成详情:');
  console.log('  - Header:', JSON.stringify(header));
  console.log('  - Payload:', JSON.stringify(payload));
  console.log('  - Token 前缀:', token.substring(0, 50) + '...');
  
  return token;
}

// 调用可灵API生成视频
async function callKlingAPI(config) {
  if (!state.klingAccessKey || state.klingAccessKey.trim() === '' ||
      !state.klingSecretKey || state.klingSecretKey.trim() === '') {
    throw new Error('请先在设置中配置可灵API密钥（访问密钥和密钥）');
  }

  // 将图片转换为base64或上传获取URL
  // 可灵API需要image_url，我们可以使用base64 data URL或者先上传图片
  // 这里我们先将图片转换为base64，然后尝试直接使用
  const imageBase64 = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      resolve(reader.result); // 包含 data:image/...;base64, 前缀
    };
    reader.onerror = reject;
    reader.readAsDataURL(config.imageFile);
  });

  // 构建提示词（根据动画类型）
  let animationPrompt = '';
  switch (config.animationType) {
    case 'zoom-in':
      animationPrompt = 'zoom in, smooth camera movement, cinematic';
      break;
    case 'zoom-out':
      animationPrompt = 'zoom out, smooth camera movement, cinematic';
      break;
    case 'pan-left':
      animationPrompt = 'pan left, smooth camera movement, cinematic';
      break;
    case 'pan-right':
      animationPrompt = 'pan right, smooth camera movement, cinematic';
      break;
    case 'pan-up':
      animationPrompt = 'pan up, smooth camera movement, cinematic';
      break;
    case 'pan-down':
      animationPrompt = 'pan down, smooth camera movement, cinematic';
      break;
    case 'rotate':
      animationPrompt = 'rotate, smooth camera movement, cinematic';
      break;
    case 'ken-burns':
      animationPrompt = 'ken burns effect, slow zoom, smooth movement, cinematic';
      break;
    case 'fade':
      animationPrompt = 'fade in, fade out, smooth transition, cinematic';
      break;
    default:
      animationPrompt = 'smooth camera movement, cinematic';
  }

  const fullPrompt = config.prompt 
    ? `${config.prompt}, ${animationPrompt}`
    : animationPrompt;

  // 解析分辨率，转换为可灵API支持的宽高比
  const [width, height] = config.resolution.split('x').map(Number);
  let aspectRatio = '16:9';
  if (width === height) {
    aspectRatio = '1:1';
  } else if (width > height) {
    aspectRatio = '16:9';
  } else {
    aspectRatio = '9:16';
  }

  // 确定视频时长（可灵API支持5秒或10秒）
  const duration = config.duration <= 5 ? 5 : 10;

  // 确定质量（根据用户设置）
  let quality = 'high';
  const defaultQuality = localStorage.getItem('defaultQuality') || 'high';
  if (defaultQuality === 'ultra') {
    quality = 'ultra';
  } else if (defaultQuality === 'standard') {
    quality = 'standard';
  }

  // 调用可灵API
  // ========== 根据可灵官方API文档配置 ==========
  // 网络协议：https
  // 请求地址：/v1/videos/image2video
  // 请求方法：POST
  // 请求格式：application/json
  // 响应格式：application/json
  // 请求头：Content-Type: application/json
  // 请求头：Authorization: 鉴权信息（参考接口鉴权）
  // ============================================
  
  // 根据官方文档，正确的端点是：/v1/videos/image2video
  // 基础URL可能是：https://api-beijing.klingai.com 或 https://api.klingai.com
  // 根据curl示例，使用：https://api-beijing.klingai.com
  
  // 如果遇到 CORS 错误，可以使用本地代理服务器
  // 代理服务器地址（如果已启动）：http://localhost:8888/proxy/kling
  // 启动代理服务器：python proxy-server.py
  const useProxy = true; // 设置为 true 以使用代理服务器（需要先启动 proxy-server.py）
  const proxyUrl = 'http://localhost:8888/proxy/kling';
  const apiBaseUrl = 'https://api-beijing.klingai.com'; // 如果不行，可以尝试 https://api.klingai.com
  const apiUrl = useProxy ? proxyUrl : `${apiBaseUrl}/v1/videos/image2video`;
  
  // 可灵API使用 JWT Token 认证（根据测试结果）
  // 使用 HS256 算法生成 JWT Token
  // 清理 API Key 中的前缀（如果用户复制时包含了 "Access Key: " 前缀）
  let cleanAccessKey = state.klingAccessKey.trim();
  if (cleanAccessKey.startsWith('Access Key:')) {
    cleanAccessKey = cleanAccessKey.replace(/^Access Key:\s*/i, '').trim();
  }
  let cleanSecretKey = state.klingSecretKey.trim();
  
  // 生成 JWT Token
  console.log('🔐 生成 JWT Token...');
  const jwtToken = await generateKlingJWTToken(cleanAccessKey, cleanSecretKey);
  console.log('✅ JWT Token 生成成功');
  
  // 使用 JWT Token 进行认证
  const authHeader = `Bearer ${jwtToken}`;
  
  const headers = {
    'Authorization': authHeader, // 鉴权信息，参考接口鉴权
    'Content-Type': 'application/json' // 数据交换格式
  };
  
  // 注意：如果遇到CORS错误，这是因为从 file:// 协议访问API时浏览器会阻止跨域请求
  // 解决方案：
  // 1. 使用本地HTTP服务器运行页面（推荐）
  // 2. 或者通过代理服务器访问API

  // 处理图片：可灵API支持base64或URL
  // 重要：如果使用base64，必须去掉 data:image/...;base64, 前缀，只保留纯base64字符串
  let imageData = imageBase64;
  if (imageBase64.startsWith('data:')) {
    // 去掉前缀，只保留base64字符串
    imageData = imageBase64.split(',')[1];
  }

  // ========== 根据可灵官方API文档构建请求体 ==========
  // 模型名称：可选，默认 kling-v1
  // 枚举值：kling-v1, kling-v1-5, kling-v1-6, kling-v2-master, kling-v2-1, kling-v2-1-master, kling-v2-5-turbo, kling-v2-6
  const modelName = 'kling-v1-6'; // 可以根据用户选择调整，默认使用 kling-v1-6

  // 模式：可选，std（标准模式，性价比高）或 pro（专家模式，高品质）
  const mode = quality === 'ultra' ? 'pro' : 'std';

  // 时长：可选，字符串 "5" 或 "10"，默认 "5"
  const durationStr = duration <= 5 ? '5' : '10';

  // 提示词长度限制：不能超过2500个字符
  const maxPromptLength = 2500;
  let finalPrompt = fullPrompt;
  if (finalPrompt && finalPrompt.length > maxPromptLength) {
    console.warn(`提示词长度超过${maxPromptLength}字符，已截断`);
    finalPrompt = finalPrompt.substring(0, maxPromptLength);
  }

  let finalNegativePrompt = config.negativePrompt || '';
  if (finalNegativePrompt && finalNegativePrompt.length > maxPromptLength) {
    console.warn(`负向提示词长度超过${maxPromptLength}字符，已截断`);
    finalNegativePrompt = finalNegativePrompt.substring(0, maxPromptLength);
  }

  // cfg_scale：可选，float，范围 [0, 1]，默认 0.5
  // 值越大，模型自由度越小，与用户输入的提示词相关性越强
  const cfgScale = Math.max(0, Math.min(1, config.strength || 0.5));

  // ========== 根据可灵官方API文档构建请求体 ==========
  // 参考：https://api-beijing.klingai.com/v1/videos/image2video
  // 注意：
  // 1. model 字段已变更为 model_name（保持向前兼容）
  // 2. Base64 图片不能包含 data:image/...;base64, 前缀
  // 3. image 参数与 image_tail 参数至少二选一
  // 4. image+image_tail、dynamic_masks/static_mask、camera_control 三选一，不能同时使用
  
  const requestBody = {
    model_name: modelName, // 模型名称，可选，默认 kling-v1，枚举值：kling-v1, kling-v1-5, kling-v1-6, kling-v2-master, kling-v2-1, kling-v2-1-master, kling-v2-5-turbo, kling-v2-6
    image: imageData, // 参考图像，必须，支持 base64（无前缀）或 URL，图片格式支持 .jpg/.jpeg/.png，大小不超过10MB，宽高不小于300px，宽高比介于1:2.5 ~ 2.5:1之间
    mode: mode, // 生成视频的模式，可选，std（标准模式，性价比高）或 pro（专家模式，高品质）
    duration: durationStr, // 生成视频时长，可选，字符串 "5" 或 "10"，默认 "5"
    cfg_scale: cfgScale // 生成视频的自由度，可选，float，范围 [0, 1]，默认 0.5，值越大，模型自由度越小，与用户输入的提示词相关性越强（kling-v2.x模型不支持）
  };
  
  // 可选参数：只有在有值时才添加，避免发送 undefined
  if (finalPrompt && finalPrompt.trim()) {
    requestBody.prompt = finalPrompt.trim(); // 正向文本提示词，可选，不能超过2500字符
  }
  
  if (finalNegativePrompt && finalNegativePrompt.trim()) {
    requestBody.negative_prompt = finalNegativePrompt.trim(); // 负向文本提示词，可选，不能超过2500字符
  }
  
  // 以下参数当前未使用，但可以根据需要添加：
  // requestBody.sound = 'off'; // 是否生成声音，on 或 off（仅V2.6及后续版本支持）
  // requestBody.voice_list = []; // 音色列表，可选，一次视频生成任务至多引用2个音色
  // requestBody.static_mask = ''; // 静态笔刷涂抹区域，可选，支持 base64 或 URL
  // requestBody.dynamic_masks = []; // 动态笔刷配置列表，可选，可配置多组（最多6组）
  // requestBody.camera_control = {}; // 控制摄像机运动的协议，可选
  // requestBody.image_tail = ''; // 参考图像-尾帧控制，可选，支持 base64 或 URL
  // requestBody.callback_url = ''; // 回调通知地址，可选
  // requestBody.external_task_id = ''; // 自定义任务ID，可选，用户自定义任务ID，单用户下需要保证唯一性
  
  // 注意：根据文档，以下参数是互斥的，不能同时使用：
  // 1. image + image_tail（至少二选一，不能同时为空）
  // 2. dynamic_masks/static_mask（运动笔刷）
  // 3. camera_control（摄像机控制）
  // 当前实现只使用 image，其他参数可以根据需要添加

  // ========== 详细诊断信息 ==========
  console.group('🔍 可灵API调用诊断信息');
  console.log('📡 API地址:', apiUrl);
  console.log('🔑 访问密钥:', state.klingAccessKey ? `${state.klingAccessKey.substring(0, 8)}...${state.klingAccessKey.substring(state.klingAccessKey.length - 4)}` : '❌ 未配置');
  console.log('🔐 密钥:', state.klingSecretKey ? `${state.klingSecretKey.substring(0, 8)}...${state.klingSecretKey.substring(state.klingSecretKey.length - 4)}` : '❌ 未配置');
  console.log('🔐 认证方式: JWT Token (HS256)');
  console.log('🔐 JWT Token 前缀:', jwtToken ? `${jwtToken.substring(0, 50)}...` : '未生成');
  console.log('📦 请求体预览:', {
    model_name: requestBody.model_name,
    prompt: requestBody.prompt,
    negative_prompt: requestBody.negative_prompt,
    mode: requestBody.mode,
    duration: requestBody.duration,
    cfg_scale: requestBody.cfg_scale,
    image: `[Base64数据，长度: ${requestBody.image.length}字符]`
  });
  console.log('🌐 当前页面协议:', window.location.protocol);
  console.log('🌐 当前页面URL:', window.location.href);
  console.groupEnd();

  // 第一次尝试：使用访问密钥
  let response;
  try {
    console.log('📤 发送第一次请求（使用访问密钥）...');
    response = await fetch(apiUrl, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(requestBody)
    });
    console.log('📥 第一次请求响应状态:', response.status, response.statusText);
    console.log('📋 响应头:', Object.fromEntries(response.headers.entries()));
  } catch (fetchError) {
    console.error('❌ 第一次请求失败（网络错误）');
    console.error('错误类型:', fetchError.name);
    console.error('错误消息:', fetchError.message);
    console.error('错误堆栈:', fetchError.stack);
    
    // 检查是否是代理服务器未运行
    if (fetchError.message.includes('Failed to fetch') && useProxy) {
      console.error('');
      console.error('🔍 诊断：代理服务器可能未运行');
      console.error('代理服务器地址:', proxyUrl);
      console.error('');
      console.error('📋 解决方案：');
      console.error('1. 打开新的命令行窗口');
      console.error('2. 运行以下命令：');
      console.error('   cd d:\\stable-diffusion-webui\\web');
      console.error('   python proxy-server.py');
      console.error('   或者双击运行: start-proxy.bat');
      console.error('3. 确保代理服务器显示 "🚀 CORS 代理服务器已启动"');
      console.error('4. 保持代理服务器窗口打开，然后重试');
      console.error('');
      throw new Error(`代理服务器连接失败。请先启动代理服务器：
1. 双击运行 start-proxy.bat
2. 或运行命令: python proxy-server.py
3. 确保代理服务器在 http://localhost:8888 运行`);
    }
    
    // 检查是否是CORS错误
    if (fetchError.message.includes('CORS') || 
        fetchError.message.includes('Failed to fetch') ||
        fetchError.name === 'TypeError') {
      console.error('🔍 诊断：这是CORS或网络连接错误');
      console.error('原因分析：');
      console.error('  1. 从 file:// 协议访问API时，浏览器会阻止跨域请求');
      console.error('  2. 或者网络连接失败（API服务器不可达）');
      console.error('  3. 或者请求被防火墙/代理阻止');
      console.error('解决方案：');
      console.error('  1. 使用HTTP服务器运行页面（推荐）');
      console.error('     - 打开命令行');
      console.error('     - 运行: cd d:\\stable-diffusion-webui\\web');
      console.error('     - 运行: python -m http.server 8000');
      console.error('     - 访问: http://localhost:8000/index.html');
      console.error('  2. 检查网络连接和防火墙设置');
      console.error('  3. 检查API服务器是否可访问');
    }
    
    throw fetchError;
  }

  if (!response.ok) {
    const errorText = await response.text();
    
    console.group('❌ 可灵API错误详情');
    console.error('HTTP状态码:', response.status);
    console.error('状态文本:', response.statusText);
    console.error('响应头:', Object.fromEntries(response.headers.entries()));
    console.error('响应内容:', errorText);
    
    // 尝试解析错误响应
    let parsedError = null;
    try {
      parsedError = JSON.parse(errorText);
      console.error('解析后的错误对象:', parsedError);
      if (parsedError.message) {
        console.error('错误消息:', parsedError.message);
      }
      if (parsedError.code) {
        console.error('错误代码:', parsedError.code);
      }
    } catch (e) {
      console.error('响应不是JSON格式，原始文本:', errorText);
    }
    
    // 如果是404错误，可能是API端点不正确
    if (response.status === 404) {
      console.error('🔍 诊断：API端点不存在');
      console.error('可能原因：');
      console.error('  1. API端点URL不正确');
      console.error('  2. 基础URL可能错误（当前: ' + apiBaseUrl + '）');
      console.error('  3. 路径可能错误（当前: /v1/videos/image2video）');
      console.error('  4. API版本可能已更新');
      console.groupEnd();
      throw new Error(`可灵API端点不存在 (404)。请检查：
1. API端点URL是否正确（当前: ${apiUrl}）
2. 访问密钥和密钥是否正确
3. 请参考可灵AI官方API文档获取正确的端点地址
错误详情: ${errorText}`);
    }
    
    // 如果是401错误，说明 JWT Token 认证失败
    if (response.status === 401) {
      console.error('🔍 诊断：认证失败');
      console.error('已尝试的认证方式：JWT Token (HS256)');
      console.error('可能原因：');
      console.error('  1. 访问密钥 (Access Key) 不正确');
      console.error('  2. 密钥 (Secret Key) 不正确');
      console.error('  3. JWT Token 生成算法不正确');
      console.error('  4. Token 已过期或被撤销');
      console.error('  5. 密钥权限不足');
      console.groupEnd();
      throw new Error(`可灵API认证失败 (401)。请检查：
1. 访问密钥 (Access Key) 是否正确（当前: ${state.klingAccessKey ? state.klingAccessKey.substring(0, 8) + '...' : '未配置'}）
2. 密钥 (Secret Key) 是否正确（当前: ${state.klingSecretKey ? state.klingSecretKey.substring(0, 8) + '...' : '未配置'}）
3. JWT Token 生成是否正确（使用 HS256 算法）
4. 如果仍然失败，请参考可灵AI官方API文档确认正确的认证方式
错误详情: ${errorText}`);
    }
    
    // 如果是403错误，可能是权限问题
    if (response.status === 403) {
      console.error('🔍 诊断：权限不足');
      console.error('可能原因：');
      console.error('  1. 账户没有访问此API的权限');
      console.error('  2. API密钥权限不足');
      console.error('  3. 需要升级账户或购买服务');
      console.error('  4. IP地址被限制');
      console.groupEnd();
      throw new Error(`可灵API权限不足 (403)。请检查：
1. 访问密钥和密钥是否正确
2. 账户是否有足够的权限
3. 请参考可灵AI官方API文档
错误详情: ${errorText}`);
    }
    
    // 其他错误
    console.error('🔍 诊断：未知错误');
    console.error('HTTP状态码:', response.status);
    console.error('请查看响应内容以获取更多信息');
    console.groupEnd();
    
    throw new Error(`可灵API调用失败: ${response.status} - ${errorText}`);
  }

  const data = await response.json();
  console.log('可灵API响应:', data);

  // ========== 根据可灵官方API文档解析响应 ==========
  // 响应格式：
  // {
  //   "code": 0, // 错误码，0 表示成功
  //   "message": "string", // 错误信息
  //   "request_id": "string", // 请求ID，系统生成，用于跟踪请求、排查问题
  //   "data": {
  //     "task_id": "string", // 任务ID，系统生成
  //     "task_info": {
  //       "external_task_id": "string" // 客户自定义任务ID
  //     },
  //     "task_status": "string", // 任务状态：submitted（已提交）、processing（处理中）、succeed（成功）、failed（失败）
  //     "created_at": 1722769557708, // 任务创建时间，Unix时间戳、单位ms
  //     "updated_at": 1722769557708 // 任务更新时间，Unix时间戳、单位ms
  //   }
  // }
  // ============================================
  
  if (data.code !== 0) {
    throw new Error(`可灵API返回错误 (code: ${data.code}): ${data.message || '未知错误'}${data.request_id ? `，请求ID: ${data.request_id}` : ''}`);
  }

  if (!data.data || !data.data.task_id) {
    throw new Error('可灵API返回格式不正确：缺少task_id。响应数据: ' + JSON.stringify(data));
  }

  const taskId = data.data.task_id;
  console.log('✅ 任务创建成功，task_id:', taskId, 'task_status:', data.data.task_status);

  // 轮询获取任务结果
  return await pollKlingTask(taskId);
}

// 轮询可灵任务状态
// 根据官方文档：/v1/videos/image2video/{task_id}
// 请求方法：GET
// 响应格式：application/json
async function pollKlingTask(taskId, maxAttempts = 60) {
  // 使用与创建任务相同的代理设置
  const useProxy = true; // 与 callKlingAPI 中的设置保持一致
  const proxyUrl = 'http://localhost:8888/proxy/kling';
  const apiBaseUrl = 'https://api-beijing.klingai.com'; // 与创建任务使用相同的基础URL
  
  // 根据官方文档，查询任务时，task_id 作为路径参数直接放在 URL 路径中
  // 请求地址：/v1/videos/image2video/{task_id}
  const apiUrl = useProxy ? `${proxyUrl}/${taskId}` : `${apiBaseUrl}/v1/videos/image2video/${taskId}`;
  
  // 使用与生成视频相同的认证方式（JWT Token）
  // 清理 API Key 中的前缀（如果用户复制时包含了 "Access Key: " 前缀）
  let cleanAccessKey = state.klingAccessKey.trim();
  if (cleanAccessKey.startsWith('Access Key:')) {
    cleanAccessKey = cleanAccessKey.replace(/^Access Key:\s*/i, '').trim();
  }
  let cleanSecretKey = state.klingSecretKey.trim();
  
  // 生成 JWT Token
  const jwtToken = await generateKlingJWTToken(cleanAccessKey, cleanSecretKey);
  const authHeader = `Bearer ${jwtToken}`;
  
  const headers = {
    'Authorization': authHeader,
    'Content-Type': 'application/json'
  };

  console.log('🔄 开始轮询任务状态，task_id:', taskId);
  console.log('📡 查询API地址:', apiUrl);

  for (let i = 0; i < maxAttempts; i++) {
    // 第一次查询前等待2秒，后续每次等待3秒
    if (i > 0) {
      await new Promise(resolve => setTimeout(resolve, 3000));
    } else {
      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    try {
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: headers
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`查询任务状态失败: ${response.status} ${response.statusText} - ${errorText}`);
      }

      const data = await response.json();
      console.log(`📊 轮询任务状态 (${i + 1}/${maxAttempts}):`, data);

      // ========== 根据官方文档解析响应 ==========
      // 响应格式：
      // {
      //   "code": 0, // 错误码；具体定义见错误码
      //   "message": "string", // 错误信息
      //   "request_id": "string", // 请求ID，系统生成，用于跟踪请求、排查问题
      //   "data": {
      //     "task_id": "string", // 任务ID，系统生成
      //     "task_status": "string", // 任务状态，枚举值：submitted（已提交）、processing（处理中）、succeed（成功）、failed（失败）
      //     "task_status_msg": "string", // 任务状态信息，当任务失败时展示失败原因
      //     "task_info": {
      //       "external_task_id": "string" // 客户自定义任务ID
      //     },
      //     "task_result": {
      //       "videos": [
      //         {
      //           "id": "string", // 生成的视频ID；全局唯一
      //           "url": "string", // 生成视频的URL
      //           "duration": "string" // 视频总时长，单位s
      //         }
      //       ]
      //     },
      //     "created_at": 1722769557708, // 任务创建时间，Unix时间戳、单位ms
      //     "updated_at": 1722769557708 // 任务更新时间，Unix时间戳、单位ms
      //   }
      // }

      // 检查API返回的错误码
      if (data.code !== 0) {
        const errorMsg = data.message || '未知错误';
        const requestId = data.request_id ? `，请求ID: ${data.request_id}` : '';
        throw new Error(`查询任务状态失败 (code: ${data.code}): ${errorMsg}${requestId}`);
      }

      if (!data.data) {
        throw new Error('API返回数据格式不正确：缺少data字段。响应数据: ' + JSON.stringify(data));
      }

      const taskStatus = data.data.task_status;
      const taskStatusMsg = data.data.task_status_msg || '';
      const requestId = data.request_id || '';
      
      console.log('📋 当前任务状态:', taskStatus);
      if (taskStatusMsg) {
        console.log('📝 状态信息:', taskStatusMsg);
      }
      if (requestId) {
        console.log('🆔 请求ID:', requestId);
      }

      // 任务状态：submitted(已提交)、processing(处理中)、succeed(成功)、failed(失败)
      if (taskStatus === 'succeed') {
        // 任务成功，获取视频URL
        if (data.data.task_result && data.data.task_result.videos && data.data.task_result.videos.length > 0) {
          const video = data.data.task_result.videos[0];
          const videoUrl = video.url;
          const videoId = video.id;
          const videoDuration = video.duration;
          
          if (videoUrl) {
            console.log('✅ 视频生成成功！');
            console.log('  - 视频ID:', videoId);
            console.log('  - 视频URL:', videoUrl);
            if (videoDuration) {
              console.log('  - 视频时长:', videoDuration, '秒');
            }
            return videoUrl;
          } else {
            throw new Error('任务成功但未找到视频URL');
          }
        } else {
          throw new Error('任务成功但未找到视频数据');
        }
      } else if (taskStatus === 'failed') {
        // 任务失败
        const errorMsg = taskStatusMsg || '任务生成失败';
        throw new Error(`任务失败: ${errorMsg}`);
      } else if (taskStatus === 'submitted' || taskStatus === 'processing') {
        // 任务进行中，继续轮询
        console.log(`⏳ 任务进行中，状态: ${taskStatus}，继续等待...`);
        if (data.data.updated_at) {
          const updatedTime = new Date(data.data.updated_at).toLocaleString();
          console.log('  - 最后更新时间:', updatedTime);
        }
        continue;
      } else {
        // 未知状态
        console.warn('⚠️ 未知任务状态:', taskStatus);
        continue;
      }
    } catch (error) {
      // 检查是否是代理服务器未运行
      if (error.message.includes('Failed to fetch') && useProxy) {
        console.error('❌ 代理服务器连接失败');
        console.error('代理服务器地址:', proxyUrl);
        console.error('');
        console.error('📋 解决方案：');
        console.error('1. 双击运行 start-proxy.bat');
        console.error('2. 或运行命令: python proxy-server.py');
        console.error('3. 确保代理服务器显示 "🚀 CORS 代理服务器已启动"');
        console.error('4. 保持代理服务器窗口打开，然后重试');
        throw new Error(`代理服务器连接失败。请先启动代理服务器：
1. 双击运行 start-proxy.bat
2. 或运行命令: python proxy-server.py
3. 确保代理服务器在 http://localhost:8888 运行`);
      }
      
      // 如果是网络错误，继续重试
      if (error.message.includes('Failed to fetch') || error.message.includes('network')) {
        console.warn(`⚠️ 网络错误 (${i + 1}/${maxAttempts}):`, error.message);
        if (i < maxAttempts - 1) {
          continue; // 继续重试
        }
      }
      // 其他错误直接抛出
      throw error;
    }
  }

  throw new Error('任务超时，请稍后重试。任务可能仍在处理中，请稍后通过任务ID查询');
}

// 客户端生成视频（简化实现）
async function generateVideoClientSide(config, imageBase64) {
  return new Promise((resolve, reject) => {
    try {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const [width, height] = config.resolution.split('x').map(Number);
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');

        // 创建视频帧
        const frames = [];
        const totalFrames = Math.floor(config.duration * config.fps);
        
        for (let i = 0; i < totalFrames; i++) {
          const progress = i / totalFrames;
          
          // 根据动画类型计算变换
          let scale = 1;
          let x = 0;
          let y = 0;
          let rotation = 0;
          let opacity = 1;

          switch (config.animationType) {
            case 'zoom-in':
              scale = 1 + (config.strength * 0.5 * progress);
              break;
            case 'zoom-out':
              scale = 1.5 - (config.strength * 0.5 * progress);
              break;
            case 'pan-left':
              x = -config.strength * 100 * progress;
              break;
            case 'pan-right':
              x = config.strength * 100 * progress;
              break;
            case 'pan-up':
              y = -config.strength * 100 * progress;
              break;
            case 'pan-down':
              y = config.strength * 100 * progress;
              break;
            case 'rotate':
              rotation = config.strength * 360 * progress;
              break;
            case 'fade':
              opacity = progress < 0.1 ? progress * 10 : (progress > 0.9 ? (1 - progress) * 10 : 1);
              break;
            case 'ken-burns':
              scale = 1 + (config.strength * 0.3 * progress);
              x = -config.strength * 50 * progress;
              y = -config.strength * 50 * progress;
              break;
          }

          // 绘制帧
          ctx.save();
          ctx.globalAlpha = opacity;
          ctx.translate(width / 2, height / 2);
          ctx.rotate((rotation * Math.PI) / 180);
          ctx.scale(scale, scale);
          ctx.drawImage(img, x - img.width / 2, y - img.height / 2, img.width, img.height);
          ctx.restore();

          frames.push(canvas.toDataURL('image/png'));
        }

        // 将帧转换为视频（简化：使用GIF或提示用户使用专业工具）
        // 注意：浏览器端生成视频需要额外的库，这里提供一个占位实现
        alert('客户端视频生成功能需要后端支持。请安装 AnimateDiff 扩展或使用其他视频生成服务。\n\n提示：您可以使用生成的图片序列在专业视频编辑软件中创建视频。');
        reject(new Error('需要后端支持视频生成功能'));
      };
      img.onerror = () => reject(new Error('图片加载失败'));
      img.src = `data:image/png;base64,${imageBase64}`;
    } catch (error) {
      reject(error);
    }
  });
}

// 复制消息内容
function copyMessage(btn) {
  const messageContent = btn.closest('.chat-message').querySelector('.message-text');
  if (messageContent) {
    const text = messageContent.textContent;
    navigator.clipboard.writeText(text).then(() => {
      btn.textContent = '已复制';
      setTimeout(() => {
        btn.textContent = '复制';
      }, 2000);
    }).catch(err => {
      console.error('复制失败:', err);
      alert('复制失败');
    });
  }
}

window.copyMessage = copyMessage;

// ========== 可灵API诊断工具 ==========
// 在浏览器控制台运行 diagnoseKlingAPI() 来诊断问题
async function diagnoseKlingAPI() {
  console.group('🔍 可灵API诊断工具');
  console.log('开始诊断可灵API连接问题...\n');
  
  const results = {
    apiKeyConfigured: false,
    networkAccessible: false,
    corsIssue: false,
    authenticationIssue: false,
    apiEndpointCorrect: false,
    recommendations: []
  };
  
  // 1. 检查API密钥配置
  console.log('1️⃣ 检查API密钥配置...');
  if (!state.klingAccessKey || state.klingAccessKey.trim() === '') {
    console.error('❌ 访问密钥未配置');
    results.recommendations.push('请在设置中配置可灵访问密钥 (Access Key)');
  } else {
    console.log('✅ 访问密钥已配置:', state.klingAccessKey.substring(0, 8) + '...' + state.klingAccessKey.substring(state.klingAccessKey.length - 4));
  }
  
  if (!state.klingSecretKey || state.klingSecretKey.trim() === '') {
    console.error('❌ 密钥未配置');
    results.recommendations.push('请在设置中配置可灵密钥 (Secret Key)');
  } else {
    console.log('✅ 密钥已配置:', state.klingSecretKey.substring(0, 8) + '...' + state.klingSecretKey.substring(state.klingSecretKey.length - 4));
  }
  
  if (state.klingAccessKey && state.klingSecretKey) {
    results.apiKeyConfigured = true;
  }
  console.log('');
  
  // 2. 检查当前页面协议
  console.log('2️⃣ 检查页面访问方式...');
  const currentProtocol = window.location.protocol;
  const currentOrigin = window.location.origin;
  console.log('当前协议:', currentProtocol);
  console.log('当前域名:', currentOrigin);
  
  if (currentProtocol === 'file:') {
    console.error('❌ 页面通过 file:// 协议访问，会导致CORS错误');
    results.corsIssue = true;
    results.recommendations.push('请通过HTTP服务器访问页面：http://localhost:8000/index.html');
  } else if (currentProtocol === 'http:' || currentProtocol === 'https:') {
    console.log('✅ 页面通过HTTP协议访问');
  }
  console.log('');
  
  // 3. 测试网络连接
  console.log('3️⃣ 测试网络连接...');
  try {
    const testUrl = 'https://api-beijing.klingai.com';
    console.log('测试连接到:', testUrl);
    
    // 使用 HEAD 请求测试连接（如果支持）
    const testResponse = await fetch(testUrl, {
      method: 'HEAD',
      mode: 'no-cors' // 使用 no-cors 来避免CORS错误，只测试网络连接
    });
    console.log('✅ 网络连接正常（无法获取详细状态，但连接成功）');
    results.networkAccessible = true;
  } catch (error) {
    console.error('❌ 网络连接失败:', error.message);
    results.recommendations.push('检查网络连接和防火墙设置');
    results.recommendations.push('检查是否可以访问 https://api-beijing.klingai.com');
  }
  console.log('');
  
  // 4. 测试API端点（带CORS检查）
  console.log('4️⃣ 测试API端点...');
  const apiUrl = 'https://api-beijing.klingai.com/v1/videos/image2video';
  console.log('API地址:', apiUrl);
  
  try {
    // 尝试发送一个简单的请求来测试CORS
    const testResponse = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.klingAccessKey || 'test'}`
      },
      body: JSON.stringify({
        model_name: 'kling-v1',
        image: 'test',
        prompt: 'test'
      })
    });
    
    console.log('✅ API端点可访问，HTTP状态:', testResponse.status);
    results.apiEndpointCorrect = true;
    
    if (testResponse.status === 401) {
      console.error('❌ 认证失败 (401)');
      results.authenticationIssue = true;
      results.recommendations.push('检查API密钥是否正确');
      results.recommendations.push('尝试使用 access_key:secret_key 格式的认证');
    } else if (testResponse.status === 404) {
      console.error('❌ API端点不存在 (404)');
      results.recommendations.push('检查API端点URL是否正确');
    }
  } catch (error) {
    if (error.message.includes('CORS') || error.message.includes('Failed to fetch')) {
      console.error('❌ CORS错误:', error.message);
      results.corsIssue = true;
      results.recommendations.push('使用代理服务器解决CORS问题（运行 proxy-server.py）');
      results.recommendations.push('在 script.js 中将 useProxy 设置为 true');
    } else {
      console.error('❌ API请求失败:', error.message);
      results.recommendations.push('检查网络连接');
    }
  }
  console.log('');
  
  // 5. 测试代理服务器
  console.log('5️⃣ 检查代理服务器...');
  try {
    const proxyUrl = 'http://localhost:8888/proxy/kling';
    const proxyResponse = await fetch(proxyUrl, {
      method: 'OPTIONS',
      mode: 'no-cors'
    });
    console.log('✅ 代理服务器可能正在运行（无法确认详细状态）');
    results.recommendations.push('如果使用代理，确保 proxy-server.py 正在运行');
  } catch (error) {
    console.warn('⚠️ 代理服务器未运行或不可访问');
    console.log('提示：如果需要使用代理，请运行: python proxy-server.py');
  }
  console.log('');
  
  // 6. 生成诊断报告
  console.log('📋 诊断报告:');
  console.log('='.repeat(50));
  console.log('API密钥配置:', results.apiKeyConfigured ? '✅' : '❌');
  console.log('网络连接:', results.networkAccessible ? '✅' : '❌');
  console.log('CORS问题:', results.corsIssue ? '❌' : '✅');
  console.log('认证问题:', results.authenticationIssue ? '❌' : '✅');
  console.log('API端点:', results.apiEndpointCorrect ? '✅' : '❌');
  console.log('='.repeat(50));
  
  if (results.recommendations.length > 0) {
    console.log('\n💡 建议的解决方案:');
    results.recommendations.forEach((rec, index) => {
      console.log(`${index + 1}. ${rec}`);
    });
  } else {
    console.log('\n✅ 所有检查通过！如果仍然失败，请查看控制台的具体错误信息。');
  }
  
  console.groupEnd();
  
  return results;
}

// 将诊断函数暴露到全局，方便在控制台调用
window.diagnoseKlingAPI = diagnoseKlingAPI;

// 确保在页面加载后立即可用
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      console.log('💡 提示：在控制台运行 diagnoseKlingAPI() 来诊断可灵API问题');
    });
  } else {
    console.log('💡 提示：在控制台运行 diagnoseKlingAPI() 来诊断可灵API问题');
  }
}

// 文件结束