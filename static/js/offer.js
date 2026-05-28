/**
 * 精彩印刷官网 - 在线报价页专用脚本
 * 功能：盒型选择、分类展开折叠、实时报价计算、文件上传、表单提交
 */

/* ===================================================
   1. 全局状态
=================================================== */
var currentBoxTypeId = null;
var currentBoxName = '';
var currentMinQty = 100;

/* ===================================================
   2. 分类展开 / 折叠
=================================================== */
function toggleCat(catId) {
  var boxes = document.getElementById('cat-boxes-' + catId);
  if (!boxes) return;
  var isOpen = boxes.style.display === 'block';
  if (isOpen) {
    boxes.style.display = 'none';
  } else {
    expandCat(catId);
  }
}

function expandCat(catId) {
  var boxes = document.getElementById('cat-boxes-' + catId);
  if (boxes) boxes.style.display = 'block';
  // 箭头旋转
  var group = document.querySelector('.offer-cat-group[data-cat-id="' + catId + '"]');
  if (group) group.classList.add('expanded');
}

/* ===================================================
   3. 选择盒型
=================================================== */
function selectBoxType(id, name, minQty) {
  currentBoxTypeId = id;
  currentBoxName = name;
  currentMinQty = minQty || 100;

  // 高亮当前选中项
  document.querySelectorAll('.offer-box-item').forEach(function (el) {
    el.classList.remove('active');
  });
  var activeEl = document.querySelector('.offer-box-item[data-bt-id="' + id + '"]');
  if (activeEl) activeEl.classList.add('active');

  // 展开对应分类
  if (activeEl) {
    var catGroup = activeEl.closest('.offer-cat-group');
    if (catGroup) {
      var catId = catGroup.getAttribute('data-cat-id');
      expandCat(parseInt(catId));
    }
  }

  // 更新表单标题
  var titleEl = document.getElementById('selectedBoxName');
  var minQtyEl = document.getElementById('offerMinQty');
  var hiddenId = document.getElementById('boxTypeId');
  if (titleEl) titleEl.textContent = name;
  if (minQtyEl) minQtyEl.textContent = '起印 ' + minQty + ' 个';
  if (hiddenId) hiddenId.value = id;

  // 显示表单，隐藏占位符
  var placeholder = document.getElementById('offerPlaceholder');
  var formWrap = document.getElementById('offerFormWrap');
  if (placeholder) placeholder.style.display = 'none';
  if (formWrap) formWrap.style.display = 'block';

  // 更新数量预设按钮
  generateQtyPresets(minQty);

  // 更新数量输入框的最小值
  var qtyInput = document.getElementById('fqty');
  if (qtyInput) {
    qtyInput.min = minQty;
    qtyInput.placeholder = '最少 ' + minQty + ' 个';
    if (!qtyInput.value || parseInt(qtyInput.value) < minQty) {
      qtyInput.value = '';
    }
  }

  // 重置报价显示
  resetPriceDisplay();

  // 滚动到表单（移动端）
  if (window.innerWidth <= 900 && formWrap) {
    formWrap.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

/* ===================================================
   4. 数量预设按钮
=================================================== */
function generateQtyPresets(minQty) {
  var wrap = document.getElementById('qtyPresets');
  if (!wrap) return;
  wrap.innerHTML = '';

  // 生成阶梯预设：minQty, minQty*2, minQty*5, minQty*10, minQty*20
  var multipliers = [1, 2, 5, 10, 20];
  multipliers.forEach(function (m) {
    var qty = minQty * m;
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'qty-preset';
    btn.setAttribute('data-qty', qty);
    btn.textContent = qty >= 1000 ? (qty / 1000) + 'k' : qty.toString();
    btn.addEventListener('click', function () {
      var input = document.getElementById('fqty');
      if (input) {
        input.value = qty;
        // 高亮选中按钮
        wrap.querySelectorAll('.qty-preset').forEach(function (b) {
          b.classList.remove('active');
        });
        btn.classList.add('active');
        // 触发自动计算
        autoCalculatePrice();
      }
    });
    wrap.appendChild(btn);
  });
}

/* ===================================================
   5. 实时报价计算
=================================================== */
function calculatePrice() {
  var boxId = currentBoxTypeId;
  var material = getSelectedMaterial();
  var qty = parseInt(document.getElementById('fqty') ? document.getElementById('fqty').value : '0');
  var length = parseFloat(document.getElementById('flen') ? document.getElementById('flen').value : '0');
  var width = parseFloat(document.getElementById('fwid') ? document.getElementById('fwid').value : '0');
  var height = parseFloat(document.getElementById('fhei') ? document.getElementById('fhei').value : '0');

  if (!boxId || !qty || qty < currentMinQty) {
    showPriceError('请填写数量（最少 ' + currentMinQty + ' 个）');
    return;
  }

  var priceBox = document.getElementById('offerPriceBox');
  var priceValue = document.getElementById('priceValue');

  // 显示加载状态
  if (priceValue) {
    priceValue.innerHTML = '<span class="price-loading">正在计算…</span>';
  }

  // 收集工艺
  var crafts = [];
  document.querySelectorAll('input[name="craft[]"]:checked').forEach(function (cb) {
    crafts.push(cb.value);
  });

  // 发送 API 请求
  fetch('/api/offer/calculate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      box_type_id: boxId,
      material: material,
      quantity: qty,
      length: length,
      width: width,
      height: height,
      crafts: crafts
    })
  })
  .then(function (res) { return res.json(); })
  .then(function (data) {
    if (data.ok && data.price_max) {
      var low = '¥' + data.price_min.toFixed(2);
      var high = '¥' + data.price_max.toFixed(2);
      var unitPrice = data.unit_price ? '（单价 ¥' + data.unit_price.toFixed(2) + '/个）' : '';
      if (priceValue) {
        priceValue.innerHTML = '<span class="price-main">' + high + '</span>' +
          '<span class="price-range"> ~ ' + low + '</span>' +
          '<span class="price-unit">' + unitPrice + '</span>';
      }
      priceBox && priceBox.classList.add('has-price');
    } else {
      showPriceError(data.msg || '暂无报价数据，请联系客服获取');
    }
  })
  .catch(function () {
    showPriceError('网络错误，请检查网络后重试');
  });
}

function autoCalculatePrice() {
  // 防抖：500ms 后自动计算
  clearTimeout(window._calcTimer);
  window._calcTimer = setTimeout(function () {
    if (currentBoxTypeId) {
      calculatePrice();
    }
  }, 500);
}

function getSelectedMaterial() {
  var checked = document.querySelector('input[name="material"]:checked');
  return checked ? checked.value : '白卡纸';
}

function resetPriceDisplay() {
  var priceValue = document.getElementById('priceValue');
  var priceBox = document.getElementById('offerPriceBox');
  if (priceValue) {
    priceValue.innerHTML = '填写数量后自动计算报价';
  }
  if (priceBox) priceBox.classList.remove('has-price');
}

function showPriceError(msg) {
  var priceValue = document.getElementById('priceValue');
  if (priceValue) {
    priceValue.innerHTML = '<span class="price-error">' + msg + '</span>';
  }
}

/* ===================================================
   6. 文件上传预览
=================================================== */
(function () {
  var fileInput = document.getElementById('fileInput');
  var uploadPreview = document.getElementById('uploadPreview');
  var uploadPlaceholder = document.querySelector('.upload-placeholder');

  if (fileInput) {
    fileInput.addEventListener('change', function () {
      var file = this.files[0];
      if (!file) return;

      // 文件大小检查（16MB）
      if (file.size > 16 * 1024 * 1024) {
        alert('文件大小不能超过 16MB');
        this.value = '';
        return;
      }

      // 显示文件信息
      if (uploadPlaceholder) uploadPlaceholder.style.display = 'none';
      if (uploadPreview) {
        var sizeStr = file.size < 1024 * 1024
          ? (file.size / 1024).toFixed(1) + ' KB'
          : (file.size / 1024 / 1024).toFixed(1) + ' MB';
        var icon = '📄';
        if (/\.(jpg|jpeg|png|gif)$/i.test(file.name)) icon = '🖼️';
        else if (/\.pdf$/i.test(file.name)) icon = '📕';
        else if (/\.(zip|rar)$/i.test(file.name)) icon = '📦';
        else if (/\.(ai|psd)$/i.test(file.name)) icon = '🎨';

        uploadPreview.innerHTML =
          '<div class="upload-file-info">' +
            '<span class="upload-file-icon">' + icon + '</span>' +
            '<div class="upload-file-detail">' +
              '<span class="upload-file-name">' + file.name + '</span>' +
              '<span class="upload-file-size">' + sizeStr + '</span>' +
            '</div>' +
            '<button type="button" class="upload-file-remove" onclick="removeFile()">✕</button>' +
          '</div>';
        uploadPreview.style.display = 'flex';
      }
    });
  }
})();

function removeFile() {
  var fileInput = document.getElementById('fileInput');
  var uploadPreview = document.getElementById('uploadPreview');
  var uploadPlaceholder = document.querySelector('.upload-placeholder');
  if (fileInput) fileInput.value = '';
  if (uploadPreview) {
    uploadPreview.innerHTML = '';
    uploadPreview.style.display = 'none';
  }
  if (uploadPlaceholder) uploadPlaceholder.style.display = 'flex';
}

/* ===================================================
   7. 表单提交
=================================================== */
(function () {
  var form = document.getElementById('offerForm');
  if (!form) return;

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    // 验证必填字段
    var fname = document.getElementById('fname');
    var fphone = document.getElementById('fphone');
    var fqty = document.getElementById('fqty');

    // 姓名
    if (!fname || !fname.value.trim()) {
      alert('请填写联系人姓名');
      fname && fname.focus();
      return;
    }

    // 手机号
    if (!fphone || !/^1[3-9]\d{9}$/.test(fphone.value.trim())) {
      alert('请填写有效的11位手机号码');
      fphone && fphone.focus();
      return;
    }

    // 数量
    var qty = parseInt(fqty ? fqty.value : '0');
    if (!qty || qty < currentMinQty) {
      alert('印刷数量最少为 ' + currentMinQty + ' 个');
      fqty && fqty.focus();
      return;
    }

    if (!currentBoxTypeId) {
      alert('请先选择盒型');
      return;
    }

    // 收集工艺
    var crafts = [];
    document.querySelectorAll('input[name="craft[]"]:checked').forEach(function (cb) {
      crafts.push(cb.value);
    });

    // 按钮loading状态
    var submitBtn = document.getElementById('submitBtn');
    var btnText = submitBtn ? submitBtn.textContent : '';
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = '提交中…';
    }

    // 构造 FormData（支持文件上传）
    var formData = new FormData(form);
    // 确保关键数据在 formData 中
    formData.set('box_type_id', currentBoxTypeId);
    formData.set('box_name', currentBoxName);
    formData.set('material', getSelectedMaterial());
    formData.set('quantity', qty);
    formData.set('crafts', crafts.join(','));

    fetch('/api/offer/submit', {
      method: 'POST',
      body: formData
    })
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = btnText;
      }
      if (data.ok) {
        // 显示成功提示
        var formEl = document.getElementById('offerForm');
        var formWrap = document.getElementById('offerFormWrap');
        var successDiv = document.getElementById('offerSuccess');
        var inquiryIdEl = document.getElementById('inquiryId');
        if (formEl) formEl.style.display = 'none';
        if (successDiv) successDiv.style.display = 'block';
        if (inquiryIdEl && data.inquiry_id) {
          inquiryIdEl.textContent = data.inquiry_id;
        }
      } else {
        alert(data.msg || '提交失败，请稍后重试');
      }
    })
    .catch(function () {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = btnText;
      }
      alert('网络错误，请检查网络后重试');
    });
  });
})();

/* ===================================================
   8. 重置询价
=================================================== */
function resetOffer() {
  var form = document.getElementById('offerForm');
  var formWrap = document.getElementById('offerFormWrap');
  var successDiv = document.getElementById('offerSuccess');

  if (form) {
    form.reset();
    form.style.display = '';
  }
  if (successDiv) successDiv.style.display = 'none';

  // 清除数量预设高亮
  document.querySelectorAll('.qty-preset').forEach(function (b) {
    b.classList.remove('active');
  });

  // 清除盒型选择
  document.querySelectorAll('.offer-box-item').forEach(function (el) {
    el.classList.remove('active');
  });

  // 重置报价显示
  resetPriceDisplay();

  // 清除文件上传
  removeFile();

  // 回到占位符
  var placeholder = document.getElementById('offerPlaceholder');
  if (placeholder && !currentBoxTypeId) {
    placeholder.style.display = 'flex';
    if (formWrap) formWrap.style.display = 'none';
  }

  // 滚动到顶部
  window.scrollTo({ top: 0, behavior: 'smooth' });

  // 重置状态但保留盒型选择（方便继续询价不同参数）
  if (currentBoxTypeId) {
    selectBoxType(currentBoxTypeId, currentBoxName, currentMinQty);
  }
}

/* ===================================================
   9. 监听输入变化，自动计算
=================================================== */
(function () {
  var qtyInput = document.getElementById('fqty');
  if (qtyInput) {
    qtyInput.addEventListener('input', autoCalculatePrice);
  }

  // 材质变更时重新计算
  document.querySelectorAll('input[name="material"]').forEach(function (radio) {
    radio.addEventListener('change', autoCalculatePrice);
  });

  // 工艺变更时重新计算
  document.querySelectorAll('input[name="craft[]"]').forEach(function (cb) {
    cb.addEventListener('change', autoCalculatePrice);
  });

  // 尺寸变更时重新计算
  ['flen', 'fwid', 'fhei'].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener('input', autoCalculatePrice);
  });
})();

/* ===================================================
   10. 初始化日志
=================================================== */
console.log('[精彩印刷] 报价页脚本加载完成 ✓');
