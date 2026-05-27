/**
 * 精彩印刷官网 - 主交互脚本
 * 功能：导航、动画、表单验证、询价提交
 */

(function() {
  'use strict';

  /* ===================================================
     1. 导航栏行为
  =================================================== */
  const header = document.getElementById('site-header');
  const hamburger = document.getElementById('hamburger');
  const mainNav = document.getElementById('main-nav');

  // 滚动添加阴影
  window.addEventListener('scroll', function() {
    if (window.scrollY > 20) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
    updateActiveNav();
    handleBackTop();
  }, { passive: true });

  // 汉堡菜单
  if (hamburger) {
    hamburger.addEventListener('click', function() {
      mainNav.classList.toggle('open');
    });
  }

  // 点击导航项关闭菜单
  document.querySelectorAll('.nav-link').forEach(function(link) {
    link.addEventListener('click', function() {
      mainNav.classList.remove('open');
    });
  });

  // 导航高亮
  function updateActiveNav() {
    const sections = ['home', 'products', 'quote', 'process', 'about', 'contact'];
    let current = '';
    sections.forEach(function(id) {
      const section = document.getElementById(id);
      if (!section) return;
      const rect = section.getBoundingClientRect();
      if (rect.top <= 100 && rect.bottom > 100) {
        current = id;
      }
    });
    document.querySelectorAll('.nav-link').forEach(function(link) {
      link.classList.remove('active');
      const href = link.getAttribute('href');
      if (href && href === '#' + current) {
        link.classList.add('active');
      }
    });
  }

  /* ===================================================
     2. 平滑滚动（兼容性处理）
  =================================================== */
  document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        const offsetTop = target.getBoundingClientRect().top + window.scrollY - 80;
        window.scrollTo({ top: offsetTop, behavior: 'smooth' });
      }
    });
  });

  /* ===================================================
     3. 返回顶部
  =================================================== */
  const backTop = document.getElementById('back-top');

  function handleBackTop() {
    if (window.scrollY > 400) {
      backTop.classList.add('visible');
    } else {
      backTop.classList.remove('visible');
    }
  }

  if (backTop) {
    backTop.addEventListener('click', function() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ===================================================
     4. 数字滚动动画
  =================================================== */
  function animateCounter(element) {
    const target = parseInt(element.getAttribute('data-count'));
    const duration = 2000;
    const start = performance.now();

    function update(currentTime) {
      const elapsed = currentTime - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.floor(eased * target);
      element.textContent = current >= 1000
        ? (current / 1000).toFixed(1).replace('.0', '') + 'k'
        : current.toString();
      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        element.textContent = target >= 1000
          ? (target / 1000).toFixed(1).replace('.0', '') + 'k'
          : target.toString();
      }
    }
    requestAnimationFrame(update);
  }

  /* ===================================================
     5. Intersection Observer 入场动画 + 数字动画
  =================================================== */
  // 添加动画类到需要动画的元素
  const animTargets = document.querySelectorAll(
    '.product-card, .adv-card, .step-item, .contact-card, .about-badge-card, .hero-content'
  );
  animTargets.forEach(function(el, i) {
    el.classList.add('animate-in');
    if (i < 4) el.classList.add('animate-delay-' + ((i % 4) + 1));
  });

  const ioOptions = { threshold: 0.15, rootMargin: '0px 0px -60px 0px' };
  const io = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        io.unobserve(entry.target);
      }
    });
  }, ioOptions);

  animTargets.forEach(function(el) { io.observe(el); });

  // 数字动画observer
  const counterEls = document.querySelectorAll('.stat-num[data-count]');
  const counterIO = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        counterIO.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });
  counterEls.forEach(function(el) { counterIO.observe(el); });

  /* ===================================================
     6. 产品卡片点击跳转询价
  =================================================== */
  document.querySelectorAll('.product-card').forEach(function(card) {
    card.addEventListener('click', function() {
      const product = this.getAttribute('data-product');
      if (product) {
        // 选中对应的产品类型
        const radio = document.querySelector('input[name="product_type"][value="' + product + '"]');
        if (radio) {
          radio.checked = true;
          // 触发change事件
          radio.dispatchEvent(new Event('change'));
        }
      }
      // 跳转到询价区域
      const quoteSection = document.getElementById('quote');
      if (quoteSection) {
        const offsetTop = quoteSection.getBoundingClientRect().top + window.scrollY - 80;
        window.scrollTo({ top: offsetTop, behavior: 'smooth' });
      }
    });
  });

  /* ===================================================
     7. 数量快捷选择
  =================================================== */
  document.querySelectorAll('.qty-preset').forEach(function(btn) {
    btn.addEventListener('click', function() {
      const qty = this.getAttribute('data-qty');
      const input = document.getElementById('order-quantity');
      if (input) {
        input.value = qty;
        input.dispatchEvent(new Event('input'));
      }
      document.querySelectorAll('.qty-preset').forEach(function(b) {
        b.style.borderColor = '';
        b.style.color = '';
        b.style.background = '';
      });
      this.style.borderColor = 'var(--primary)';
      this.style.color = 'var(--primary)';
      this.style.background = 'rgba(232, 75, 54, 0.06)';
    });
  });

  /* ===================================================
     8. 表单验证
  =================================================== */
  function showError(fieldId, message) {
    const input = document.getElementById(fieldId);
    const errEl = document.getElementById('error-' + fieldId.replace('contact-', '').replace('order-', '').replace('size-', '').replace('-', '-'));
    if (input) input.classList.add('error');
    // 查找最近的error元素
    if (input) {
      const errorDiv = input.parentElement.querySelector('.form-error')
        || input.closest('.form-group')?.querySelector('.form-error');
      if (errorDiv) errorDiv.textContent = message;
    }
  }

  function clearError(input) {
    input.classList.remove('error');
    const errorDiv = input.parentElement.querySelector('.form-error')
      || input.closest('.form-group')?.querySelector('.form-error')
      || input.closest('.size-field')?.querySelector('.form-error');
    if (errorDiv) errorDiv.textContent = '';
  }

  function setFieldError(inputEl, errorEl, message) {
    if (inputEl) inputEl.classList.add('error');
    if (errorEl) errorEl.textContent = message;
  }

  function clearFieldError(inputEl, errorEl) {
    if (inputEl) inputEl.classList.remove('error');
    if (errorEl) errorEl.textContent = '';
  }

  // 实时验证
  const nameInput  = document.getElementById('contact-name');
  const phoneInput = document.getElementById('contact-phone');
  const qtyInput   = document.getElementById('order-quantity');
  const lenInput   = document.getElementById('size-length');
  const widInput   = document.getElementById('size-width');

  function addRealTimeValidation(input, errId, validator) {
    if (!input) return;
    const errEl = document.getElementById(errId);
    input.addEventListener('blur', function() {
      const msg = validator(this.value);
      if (msg) setFieldError(this, errEl, msg);
      else clearFieldError(this, errEl);
    });
    input.addEventListener('input', function() {
      if (this.classList.contains('error')) {
        const msg = validator(this.value);
        if (!msg) clearFieldError(this, errEl);
      }
    });
  }

  addRealTimeValidation(nameInput, 'error-name', function(v) {
    if (!v.trim()) return '请输入联系人姓名';
    return '';
  });
  addRealTimeValidation(phoneInput, 'error-phone', function(v) {
    if (!v.trim()) return '请输入手机号码';
    if (!/^1[3-9]\d{9}$/.test(v.trim())) return '请输入有效的手机号码';
    return '';
  });
  addRealTimeValidation(qtyInput, 'error-quantity', function(v) {
    if (!v || parseInt(v) < 1) return '请输入有效的订购数量';
    return '';
  });
  addRealTimeValidation(lenInput, 'error-length', function(v) {
    if (!v || parseInt(v) < 10) return '请输入有效长度（≥10mm）';
    return '';
  });
  addRealTimeValidation(widInput, 'error-width', function(v) {
    if (!v || parseInt(v) < 10) return '请输入有效宽度（≥10mm）';
    return '';
  });

  /* ===================================================
     9. 表单提交
  =================================================== */
  const quoteForm = document.getElementById('quoteForm');
  const formSuccess = document.getElementById('form-success');
  const submitBtn = document.getElementById('submit-btn');
  const newQuoteBtn = document.getElementById('new-quote-btn');

  function validateForm() {
    let valid = true;
    const errors = [];

    // 姓名
    const nameVal = nameInput ? nameInput.value.trim() : '';
    const nameErr = document.getElementById('error-name');
    if (!nameVal) {
      setFieldError(nameInput, nameErr, '请输入联系人姓名');
      valid = false;
    } else clearFieldError(nameInput, nameErr);

    // 电话
    const phoneVal = phoneInput ? phoneInput.value.trim() : '';
    const phoneErr = document.getElementById('error-phone');
    if (!phoneVal) {
      setFieldError(phoneInput, phoneErr, '请输入手机号码');
      valid = false;
    } else if (!/^1[3-9]\d{9}$/.test(phoneVal)) {
      setFieldError(phoneInput, phoneErr, '请输入有效的11位手机号码');
      valid = false;
    } else clearFieldError(phoneInput, phoneErr);

    // 产品类型
    const productType = document.querySelector('input[name="product_type"]:checked');
    const typeErr = document.getElementById('error-product-type');
    if (!productType) {
      if (typeErr) typeErr.textContent = '请选择产品类型';
      valid = false;
    } else {
      if (typeErr) typeErr.textContent = '';
    }

    // 长度
    const lenVal = lenInput ? lenInput.value : '';
    const lenErr = document.getElementById('error-length');
    if (!lenVal || parseInt(lenVal) < 10) {
      setFieldError(lenInput, lenErr, '请输入有效长度（≥10mm）');
      valid = false;
    } else clearFieldError(lenInput, lenErr);

    // 宽度
    const widVal = widInput ? widInput.value : '';
    const widErr = document.getElementById('error-width');
    if (!widVal || parseInt(widVal) < 10) {
      setFieldError(widInput, widErr, '请输入有效宽度（≥10mm）');
      valid = false;
    } else clearFieldError(widInput, widErr);

    // 数量
    const qtyVal = qtyInput ? qtyInput.value : '';
    const qtyErr = document.getElementById('error-quantity');
    if (!qtyVal || parseInt(qtyVal) < 1) {
      setFieldError(qtyInput, qtyErr, '请输入订购数量（最少1件）');
      valid = false;
    } else clearFieldError(qtyInput, qtyErr);

    return valid;
  }

  if (quoteForm) {
    quoteForm.addEventListener('submit', function(e) {
      e.preventDefault();

      if (!validateForm()) {
        // 滚动到第一个错误
        const firstError = quoteForm.querySelector('.error');
        if (firstError) {
          const top = firstError.getBoundingClientRect().top + window.scrollY - 120;
          window.scrollTo({ top: top, behavior: 'smooth' });
        }
        return;
      }

      // 收集数据
      const formData = collectFormData();

      // 模拟提交（显示loading状态）
      submitBtn.disabled = true;
      submitBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite;">
          <circle cx="12" cy="12" r="10" stroke-dasharray="60" stroke-dashoffset="60" opacity="0.3"/>
          <path d="M12 2a10 10 0 010 20"/>
        </svg>
        提交中...
      `;

      // 模拟API调用 (2秒后显示成功)
      setTimeout(function() {
        quoteForm.style.display = 'none';
        formSuccess.style.display = 'block';
        // 打印到console（实际项目替换为API调用）
        console.log('询价数据:', formData);
        submitBtn.disabled = false;
      }, 1500);
    });
  }

  function collectFormData() {
    const processChecked = Array.from(
      document.querySelectorAll('input[name="process[]"]:checked')
    ).map(function(c) { return c.value; });

    const productTypeEl = document.querySelector('input[name="product_type"]:checked');

    return {
      name: nameInput ? nameInput.value.trim() : '',
      phone: phoneInput ? phoneInput.value.trim() : '',
      company: (document.getElementById('company-name') || {}).value || '',
      email: (document.getElementById('contact-email') || {}).value || '',
      product_type: productTypeEl ? productTypeEl.value : '',
      size: {
        length: (document.getElementById('size-length') || {}).value || '',
        width: (document.getElementById('size-width') || {}).value || '',
        height: (document.getElementById('size-height') || {}).value || ''
      },
      quantity: qtyInput ? qtyInput.value : '',
      quantity_unit: (document.getElementById('quantity-unit') || {}).value || '个',
      material: (document.getElementById('material') || {}).value || '',
      processes: processChecked,
      remarks: (document.getElementById('remarks') || {}).value || '',
      submitted_at: new Date().toISOString()
    };
  }

  // 重新询价
  if (newQuoteBtn) {
    newQuoteBtn.addEventListener('click', function() {
      formSuccess.style.display = 'none';
      quoteForm.style.display = '';
      quoteForm.reset();
      // 清除所有错误
      quoteForm.querySelectorAll('.form-error').forEach(function(el) {
        el.textContent = '';
      });
      quoteForm.querySelectorAll('.error').forEach(function(el) {
        el.classList.remove('error');
      });
      submitBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
        提交询价申请
      `;
    });
  }

  /* ===================================================
     10. 旋转动画 CSS 注入
  =================================================== */
  const spinStyle = document.createElement('style');
  spinStyle.textContent = '@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }';
  document.head.appendChild(spinStyle);

  /* ===================================================
     11. 悬浮卡片微动画（Hero）
  =================================================== */
  const heroCards = document.querySelectorAll('.hero-card');
  let mouseX = 0, mouseY = 0;

  document.addEventListener('mousemove', function(e) {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
  }, { passive: true });

  let rafId;
  function animateCards() {
    heroCards.forEach(function(card, i) {
      const depth = (i + 1) * 3;
      const tx = mouseX * depth;
      const ty = mouseY * depth;
      card.style.transform = card.classList.contains('card-back')
        ? `rotate(3deg) translate(${tx}px, ${ty}px)`
        : card.classList.contains('card-mid')
          ? `rotate(-1.5deg) translate(${tx * 0.7}px, ${ty * 0.7}px)`
          : `translate(${tx * 0.4}px, ${ty * 0.4}px)`;
    });
    rafId = requestAnimationFrame(animateCards);
  }

  // 仅在桌面端且无reduced motion时启用
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const isDesktop = window.innerWidth > 900;

  if (isDesktop && !prefersReducedMotion) {
    animateCards();
  }

  /* ===================================================
     12. 清理
  =================================================== */
  window.addEventListener('beforeunload', function() {
    if (rafId) cancelAnimationFrame(rafId);
  });

  /* ===================================================
     初始化完成
  =================================================== */
  console.log('[精彩印刷] 页面初始化完成 ✓');
})();
