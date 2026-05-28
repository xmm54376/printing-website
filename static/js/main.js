/**
 * 精彩印刷官网 - 全站主交互脚本（升级版）
 * 对标：智盒包装 + 聚意印刷
 * 功能：导航栏、轮播、动画、浮动客服、表单
 */

(function () {
  'use strict';

  /* ===================================================
     1. 导航栏行为
  =================================================== */
  const header = document.getElementById('siteHeader');
  const hamburger = document.getElementById('hamburger');
  const mobileNav = document.getElementById('mobileNav');

  // 滚动添加阴影
  if (header) {
    window.addEventListener('scroll', function () {
      header.classList.toggle('scrolled', window.scrollY > 20);
      handleBackTop();
    }, { passive: true });
  }

  // 汉堡菜单切换
  if (hamburger && mobileNav) {
    hamburger.addEventListener('click', function () {
      hamburger.classList.toggle('active');
      mobileNav.classList.toggle('open');
      // 防止 body 滚动
      document.body.classList.toggle('nav-open');
    });

    // 点击移动端导航项后关闭
    mobileNav.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        hamburger.classList.remove('active');
        mobileNav.classList.remove('open');
        document.body.classList.remove('nav-open');
      });
    });
  }

  /* ===================================================
     2. 用户下拉菜单
  =================================================== */
  const userMenu = document.querySelector('.user-menu');
  if (userMenu) {
    const btn = userMenu.querySelector('.btn-user');
    const dropdown = userMenu.querySelector('.user-dropdown');
    if (btn && dropdown) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        dropdown.classList.toggle('show');
      });
      // 点击外部关闭
      document.addEventListener('click', function (e) {
        if (!userMenu.contains(e.target)) {
          dropdown.classList.remove('show');
        }
      });
    }
  }

  /* ===================================================
     3. 平滑滚动（锚点链接）
  =================================================== */
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
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
     4. 返回顶部按钮
  =================================================== */
  const backTop = document.getElementById('backTop');

  function handleBackTop() {
    if (backTop) {
      backTop.classList.toggle('visible', window.scrollY > 400);
    }
  }

  // 初始触发一次
  handleBackTop();

  /* ===================================================
     5. 数字滚动动画
  =================================================== */
  function animateCounter(element) {
    const target = parseInt(element.getAttribute('data-target'), 10);
    if (isNaN(target)) return;
    const unit = element.nextElementSibling; // stat-unit
    const duration = 2000;
    const start = performance.now();

    function update(currentTime) {
      const elapsed = currentTime - start;
      const progress = Math.min(elapsed / duration, 1);
      // easeOutCubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.floor(eased * target);
      element.textContent = current.toLocaleString();
      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        element.textContent = target.toLocaleString();
      }
    }
    requestAnimationFrame(update);
  }

  /* ===================================================
     6. Intersection Observer - 入场动画 + 数字动画
  =================================================== */
  // 为需要动画的元素添加基础 class
  const animSelectors = [
    '.category-card', '.service-card', '.adv-card',
    '.step', '.contact-card', '.stock-card',
    '.banner-text > *'
  ];
  const animTargets = document.querySelectorAll(animSelectors.join(', '));

  const ioOptions = { threshold: 0.12, rootMargin: '0px 0px -50px 0px' };
  const io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        io.unobserve(entry.target);
      }
    });
  }, ioOptions);

  animTargets.forEach(function (el) {
    if (!el.classList.contains('animate-in')) {
      el.classList.add('animate-in');
    }
    io.observe(el);
  });

  // 数字动画 Observer
  const counterEls = document.querySelectorAll('.stat-num[data-target]');
  const counterIO = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        counterIO.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });
  counterEls.forEach(function (el) { counterIO.observe(el); });

  /* ===================================================
     8. offer页面兼容处理
  =================================================== */
  // 为不支持 :has() 的浏览器提供padding-top
  if (document.querySelector('.offer-page')) {
    document.body.style.paddingTop = 'var(--header-h)';
  }

  /* ===================================================
     9. 旋转动画 CSS 注入
  =================================================== */
  const extraStyles = document.createElement('style');
  extraStyles.textContent = [
    '@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }',
    '.nav-open { overflow: hidden; }'
  ].join('\n');
  document.head.appendChild(extraStyles);

  /* ===================================================
     10. 初始化完成日志
  =================================================== */
  console.log('[精彩印刷] 主脚本加载完成 ✓');

})();
