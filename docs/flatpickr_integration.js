/**
 * Flatpickr日期选择器集成方案
 * 实现4位年份后自动跳转到月份
 */

// 1. 在base.html的<head>中添加Flatpickr资源
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
<script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
<script src="https://cdn.jsdelivr.net/npm/flatpickr/dist/l10n/zh.js"></script>

// 2. 初始化脚本（替换现有的日期优化脚本）
<script>
(function() {
    function initFlatpickr() {
        const dateInputs = document.querySelectorAll('input[type="date"]');

        dateInputs.forEach(function(input) {
            // 转换为text类型，防止浏览器原生日期选择器
            input.type = 'text';

            // 初始化Flatpickr
            flatpickr(input, {
                locale: 'zh',  // 中文界面
                dateFormat: 'Y-m-d',  // 日期格式
                allowInput: true,  // 允许手动输入

                // 自定义年份输入行为
                onOpen: function(selectedDates, dateStr, instance) {
                    // 监听年份输入框
                    const yearInput = instance.yearElements[0];
                    if (yearInput) {
                        yearInput.addEventListener('input', function(e) {
                            const value = e.target.value;
                            // 输入4位数字后自动跳转到月份
                            if (value.length === 4 && /^\d{4}$/.test(value)) {
                                setTimeout(function() {
                                    const monthSelect = instance.monthElements[0];
                                    if (monthSelect) {
                                        monthSelect.focus();
                                    }
                                }, 50);
                            }
                        });
                    }
                }
            });
        });
    }

    // 页面加载后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initFlatpickr);
    } else {
        initFlatpickr();
    }

    // 提供全局函数供动态页面使用
    window.initFlatpickr = initFlatpickr;
})();
</script>

/**
 * 说明：
 * 1. Flatpickr是一个轻量级日期选择器库（~6KB gzipped）
 * 2. 支持完全自定义，包括年份输入框的行为
 * 3. 提供中文界面，用户体验好
 * 4. 跨浏览器一致性好
 *
 * 效果：
 * - 用户输入4位年份（如2025）
 * - 光标自动跳转到月份选择框
 * - 不再需要输入6位数字
 */
