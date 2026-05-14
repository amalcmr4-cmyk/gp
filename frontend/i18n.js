// i18n.js — DataWizard Bilingual System (AR / EN)
// Handles translation, RTL, and language toggle across all pages.

(function () {
    'use strict';

    // ═══════════════════════════════════════════════════
    //  Translation Dictionary
    // ═══════════════════════════════════════════════════
    const dict = {
        // ── Navbar & General ──
        signUp:          { en: 'Sign Up',              ar: 'إنشاء حساب' },
        logIn:           { en: 'Log In',               ar: 'تسجيل الدخول' },
        newAnalysis:     { en: 'New Analysis',         ar: 'تحليل جديد' },
        saveReport:      { en: 'Save Report',          ar: 'حفظ التقرير' },

        // ── Sidebar ──
        newChat:         { en: 'New Chat',             ar: 'محادثة جديدة' },
        newUpload:       { en: 'New Upload',           ar: 'رفع جديد' },
        uploadNew:       { en: 'Upload New Data',      ar: 'رفع بيانات جديدة' },
        uploadData:      { en: 'Upload Data',          ar: 'رفع البيانات' },
        dashboard:       { en: 'Dashboard',            ar: 'لوحة التحكم' },
        analysis:        { en: 'Analysis',             ar: 'التحليل' },
        history:         { en: 'History',              ar: 'السجل' },
        settings:        { en: 'Settings',             ar: 'الإعدادات' },
        terms:           { en: 'Terms & Policies',     ar: 'الشروط والسياسات' },

        // ── Home Page ──
        heroTry:         { en: 'Try',                  ar: 'جرّب' },
        heroSubtitle:    { en: 'and uncover the hidden magic in your data in seconds', ar: 'واكتشف السحر المخفي في بياناتك خلال ثوانٍ' },
        uploadTitle:     { en: 'Upload your data file here', ar: 'ارفع ملف بياناتك هنا' },
        uploadDesc:      { en: 'We support CSV and Excel files', ar: 'ندعم ملفات CSV و Excel' },
        startAnalysis:   { en: 'start analysis now',   ar: 'ابدأ التحليل الآن' },
        noFileSelected:  { en: 'No file selected',     ar: 'لم يتم اختيار ملف' },
        saveAs:          { en: 'Save Analysis As',     ar: 'حفظ التحليل باسم' },
        whatName:        { en: 'What would you like to name this report?', ar: 'ما الاسم الذي تريد إعطاءه لهذا التقرير؟' },
        enterFileName:   { en: 'Enter file name...',   ar: 'أدخل اسم الملف...' },
        continueToAnalysis: { en: 'Continue to Analysis', ar: 'متابعة التحليل' },

        // ── Steps Cards ──
        step1Title:      { en: 'Secure Upload',        ar: 'رفع آمن' },
        step1Desc:       { en: 'Your data is processed in memory and encrypted. We never train our models on your private data.', ar: 'بياناتك تُعالج في الذاكرة ومشفّرة. لا نستخدم بياناتك الخاصة في تدريب نماذجنا.' },
        step2Title:      { en: 'AI-Powered Analysis',   ar: 'تحليل بالذكاء الاصطناعي' },
        step2Desc:       { en: 'Our advanced AI instantly detects patterns, anomalies, and correlations you might have missed.', ar: 'ذكاؤنا الاصطناعي المتقدم يكتشف فوراً الأنماط والشذوذ والعلاقات التي ربما فاتتك.' },
        step2Link:       { en: 'Start analysis now',    ar: 'ابدأ التحليل الآن' },
        step3Title:      { en: 'Actionable Insights',   ar: 'رؤى قابلة للتنفيذ' },
        step3Desc:       { en: 'Beautifully rendered visualizations and clear, strategic recommendations ready for your presentation.', ar: 'رسوم بيانية جميلة وتوصيات استراتيجية واضحة جاهزة لعرضك التقديمي.' },

        // ── Footer ──
        encryption:      { en: '256-bit Encryption',   ar: 'تشفير 256-بت' },
        dataNotStored:   { en: 'Data Never Stored',    ar: 'البيانات لا تُخزّن' },
        gdpr:            { en: 'GDPR Compliant',       ar: 'متوافق مع GDPR' },
        footerRights:    { en: '© 2026 DataWizard – All rights reserved.', ar: '© 2026 DataWizard – جميع الحقوق محفوظة.' },
        footerPrivacy:   { en: 'Your data privacy & security is our top priority', ar: 'خصوصية وأمان بياناتك هي أولويتنا القصوى' },
        footerBiz:       { en: '© 2026 DataWizard – Business Analytics Platform', ar: '© 2026 DataWizard – منصة تحليل الأعمال' },

        // ── Login Page ──
        welcomeBack:     { en: 'Welcome Back',         ar: 'مرحباً بعودتك' },
        signInAccount:   { en: 'Sign in to your account', ar: 'سجّل دخولك إلى حسابك' },
        email:           { en: 'Email',                ar: 'البريد الإلكتروني' },
        password:        { en: 'Password',             ar: 'كلمة المرور' },
        emailPlaceholder:{ en: 'Enter your email',     ar: 'أدخل بريدك الإلكتروني' },
        passPlaceholder: { en: 'Enter password',       ar: 'أدخل كلمة المرور' },
        signInBtn:       { en: 'Sign In',              ar: 'تسجيل الدخول' },
        forgotPass:      { en: 'Forgot password?',     ar: 'نسيت كلمة المرور؟' },
        noAccount:       { en: "Don't have an account?", ar: 'ليس لديك حساب؟' },
        signUpLink:      { en: 'Sign up',              ar: 'إنشاء حساب' },
        authenticating:  { en: 'Authenticating...',     ar: 'جارٍ التحقق...' },

        // ── Signup Page ──
        signUpTitle:     { en: 'Sign Up',              ar: 'إنشاء حساب' },
        signUpSubtitle:  { en: "Let's get started with your 30 days free trial", ar: 'لنبدأ مع فترتك التجريبية المجانية لمدة 30 يوم' },
        name:            { en: 'Name',                 ar: 'الاسم' },
        namePlaceholder: { en: 'Enter your name',      ar: 'أدخل اسمك' },
        signUpBtn:       { en: 'Sign Up',              ar: 'إنشاء حساب' },
        alreadyAccount:  { en: 'Already have an account?', ar: 'لديك حساب بالفعل؟' },
        logInLink:       { en: 'Log In',               ar: 'تسجيل الدخول' },
        termsText:       { en: 'By signing up, you agree to our', ar: 'بتسجيلك، أنت توافق على' },
        termsOfUse:      { en: 'Terms of Use',         ar: 'شروط الاستخدام' },
        andWord:         { en: 'and',                  ar: 'و' },
        privacyPolicy:   { en: 'Privacy Policy',       ar: 'سياسة الخصوصية' },
        creatingAccount: { en: 'Creating Account...',   ar: 'جارٍ إنشاء الحساب...' },

        // ── History Page ──
        historyTitle:    { en: 'Analysis History',     ar: 'سجل التحليلات' },
        historySubtitle: { en: 'Your recent analysis sessions (stored locally)', ar: 'جلسات التحليل الأخيرة (مخزنة محلياً)' },
        clearAll:        { en: 'Clear All',            ar: 'مسح الكل' },
        noHistory:       { en: 'No Analysis History',  ar: 'لا يوجد سجل تحليلات' },
        noHistoryDesc:   { en: "You haven't analyzed any files yet. Upload a file to get started!", ar: 'لم تقم بتحليل أي ملفات بعد. ارفع ملفاً للبدء!' },
        uploadNow:       { en: 'Upload Now',           ar: 'ارفع الآن' },
        cancel:          { en: 'Cancel',               ar: 'إلغاء' },
        deleteRecord:    { en: 'Delete this record?',  ar: 'حذف هذا السجل؟' },
        deleteAll:       { en: 'Delete all history?',  ar: 'حذف كل السجل؟' },
        cannotUndo:      { en: 'This action cannot be undone.', ar: 'لا يمكن التراجع عن هذا الإجراء.' },
        deleteBtn:       { en: 'Delete',               ar: 'حذف' },
        openAgain:       { en: 'Open Again',           ar: 'فتح مجدداً' },
        report:          { en: 'Report',               ar: 'التقرير' },
        rows:            { en: 'rows',                 ar: 'صفوف' },
        columns:         { en: 'columns',              ar: 'أعمدة' },

        // ── Analysis Page ──
        fileName:        { en: 'File Name',            ar: 'اسم الملف' },
        totalRows:       { en: 'Total Rows',           ar: 'إجمالي الصفوف' },
        totalCols:       { en: 'Total Columns',        ar: 'إجمالي الأعمدة' },
        completeness:    { en: 'Completeness',         ar: 'الاكتمال' },
        missingCells:    { en: 'Missing Cells',        ar: 'خلايا مفقودة' },
        numericCols:     { en: 'Numeric Columns',      ar: 'أعمدة رقمية' },
        loadingMsg:      { en: 'The Wizard is analyzing your data...', ar: 'المعالج يقوم بتحليل بياناتك...' },
        errorTitle:      { en: 'Oops! Something went wrong', ar: 'عذراً! حدث خطأ ما' },
        noFileId:        { en: 'No file ID found. Please upload a file first.', ar: 'لم يتم العثور على معرّف الملف. الرجاء رفع ملف أولاً.' },
        backHome:        { en: 'Back to Home',         ar: 'العودة للرئيسية' },
        basicAnalysis:   { en: 'Basic Analysis',       ar: 'التحليل الأساسي' },
        advancedInsights:{ en: 'AI Advanced Insights',  ar: 'رؤى الذكاء الاصطناعي المتقدمة' },
        dataPreview:     { en: 'Data Preview',         ar: 'معاينة البيانات' },
        searchData:      { en: 'Search data...',       ar: 'بحث في البيانات...' },
        cleanData:       { en: 'Clean Data',           ar: 'تنظيف البيانات' },
        exportCSV:       { en: 'Export CSV',            ar: 'تصدير CSV' },
        columnAnalysis:  { en: 'Column Analysis Details', ar: 'تفاصيل تحليل الأعمدة' },
        numericStats:    { en: 'Numeric Statistics',    ar: 'الإحصائيات الرقمية' },
        correlation:     { en: 'Correlation Matrix',    ar: 'مصفوفة الارتباط' },
        visualizations:  { en: 'Data Visualizations',   ar: 'الرسوم البيانية' },
        aiInsights:      { en: 'AI Business Insights',  ar: 'رؤى الأعمال بالذكاء الاصطناعي' },
        executiveSummary:{ en: 'Executive Summary',     ar: 'الملخص التنفيذي' },
        pricingStrategy: { en: 'Pricing Strategy',      ar: 'استراتيجية التسعير' },
        growthOpp:       { en: 'Growth Opportunities',  ar: 'فرص النمو' },
        customerStrategy:{ en: 'Customer Strategy',     ar: 'استراتيجية العملاء' },
        riskAlerts:      { en: 'Risk Alerts',           ar: 'تنبيهات المخاطر' },
        globalComparison:{ en: 'Global Comparison',     ar: 'المقارنة العالمية' },
        forecast:        { en: 'Forecast',              ar: 'التوقعات' },
        aiChartSugg:     { en: 'AI Chart Suggestion',   ar: 'اقتراح رسم بياني بالذكاء الاصطناعي' },
        exportReport:    { en: 'Export Report',         ar: 'تصدير التقرير' },
        exportSubtitle:  { en: 'Choose your preferred export format', ar: 'اختر صيغة التصدير المفضلة' },
        exportJSON:      { en: 'Export JSON',           ar: 'تصدير JSON' },
        exportJSONDesc:  { en: 'Full raw data & insights', ar: 'البيانات الكاملة والرؤى' },
        exportPDF:       { en: 'Print View',            ar: 'عرض الطباعة' },
        exportPDFDesc:   { en: 'Open browser print dialog', ar: 'فتح نافذة الطباعة' },
        exportServerPDF: { en: 'Download PDF Report',   ar: 'تحميل تقرير PDF' },
        exportServerPDFDesc: { en: 'Generated by AI DataWizard', ar: 'مُنشأ بواسطة DataWizard AI' },

        // ── Report Page ──
        execAudit:       { en: 'Executive Data Audit',  ar: 'تدقيق البيانات التنفيذي' },
        reportId:        { en: 'Report ID',             ar: 'معرّف التقرير' },
        generatedOn:     { en: 'Generated on',          ar: 'أُنشئ في' },
        fileNameLabel:   { en: 'File Name',             ar: 'اسم الملف' },
        fileSize:        { en: 'File Size',             ar: 'حجم الملف' },
        uploadedAt:      { en: 'Uploaded At',           ar: 'تاريخ الرفع' },
        totalAnalyses:   { en: 'Total Analyses',        ar: 'إجمالي التحليلات' },
        printReport:     { en: 'Print Report',          ar: 'طباعة التقرير' },
        loadingReport:   { en: 'Loading Executive Report...', ar: 'جارٍ تحميل التقرير التنفيذي...' },
        analysisRun:     { en: 'Analysis Run',          ar: 'دورة التحليل' },
        dataQuality:     { en: 'Data Quality',          ar: 'جودة البيانات' },
        rowsLabel:       { en: 'Rows',                  ar: 'صفوف' },
        colsLabel:       { en: 'Cols',                  ar: 'أعمدة' },

        // ── Chatbot ──
        chatTitle:       { en: 'DataWizard AI',         ar: 'DataWizard AI' },
        chatWelcomeTitle:{ en: 'DataWizard AI Analyst',  ar: 'محلل DataWizard الذكي' },
        chatWelcomeSub:  { en: "Hello! I'm your smart data analyst. You can ask me anything about your data (calculations, sales, predictions).", ar: 'مرحباً! أنا محلل البيانات الذكي الخاص بك. يمكنك سؤالي عن أي شيء يخص بياناتك (حسابات، مبيعات، توقعات).' },
        chatChip1:       { en: '💰 Calculate Total',     ar: '💰 حساب الإجمالي' },
        chatChip1Q:      { en: 'Calculate total sales',  ar: 'احسب لي إجمالي المبيعات' },
        chatChip2:       { en: '🔮 Predict Trends',      ar: '🔮 توقع الاتجاهات' },
        chatChip2Q:      { en: 'Predict future data trends', ar: 'توقع الاتجاهات المستقبلية للبيانات' },
        chatChip3:       { en: '🔍 Outliers',            ar: '🔍 القيم الشاذة' },
        chatChip3Q:      { en: 'Extract outliers from the data', ar: 'استخرج لي القيم الشاذة في البيانات' },
        chatChip4:       { en: '📊 Statistical Summary',  ar: '📊 ملخص إحصائي' },
        chatChip4Q:      { en: 'Give me a comprehensive statistical summary', ar: 'اعطني ملخص إحصائي شامل' },
        chatPlaceholder: { en: 'Ask anything (e.g. calculate monthly sales)...', ar: 'اسأل أي شيء (مثال: احسب مبيعات الشهر)...' },
        chatThinking:    { en: 'Reading data and calculating...', ar: 'يقوم بقراءة البيانات والحساب...' },
        chatCopy:        { en: 'Copy',                   ar: 'نسخ' },
        chatNoFile:      { en: '⚠️ Please upload a file or open an analysis first so I can help you read your data.', ar: '⚠️ الرجاء رفع ملف أو فتح تحليل أولاً لكي أتمكن من مساعدتك في قراءة بياناتك.' },
        chatNoFileData:  { en: '⚠️ Please upload a data file first so I can perform calculations and analysis.', ar: '⚠️ الرجاء رفع ملف بيانات أولاً حتى أتمكن من إجراء الحسابات والتحليل عليه.' },
        chatNoResponse:  { en: 'Could not find a response, please try again.', ar: 'لم أتمكن من إيجاد استجابة، يرجى المحاولة مرة أخرى.' },
        chatServerError: { en: 'A server error occurred while fetching the answer.', ar: 'حدث خطأ في الخادم أثناء جلب الإجابة.' },
        chatConnError:   { en: '⚠️ Connection error: ', ar: '⚠️ خطأ في الاتصال: ' },

        // ── Toasts ──
        selectFileFirst: { en: 'Please select a file first', ar: 'الرجاء اختيار ملف أولاً' },
        uploadSuccess:   { en: 'File uploaded successfully!', ar: 'تم رفع الملف بنجاح!' },
        uploadError:     { en: 'Error: ',               ar: 'خطأ: ' },
        dashboardToast:  { en: 'Please upload data to get a Personalized Dashboard', ar: 'الرجاء رفع بيانات للحصول على لوحة تحكم مخصصة' },
        startAnalysisBtn:{ en: 'Start Analysis Now',    ar: 'ابدأ التحليل الآن' },
        uploading:       { en: 'Uploading...',          ar: 'جارٍ الرفع...' },
    };

    // ═══════════════════════════════════════════════════
    //  Core Functions
    // ═══════════════════════════════════════════════════
    const STORAGE_KEY = 'dw-lang';

    function getCurrentLang() {
        return localStorage.getItem(STORAGE_KEY) || 'en';
    }

    /** Get translated text by key */
    function t(key) {
        const lang = getCurrentLang();
        if (dict[key]) return dict[key][lang] || dict[key]['en'] || key;
        return key;
    }

    /** Apply all data-i18n attributes on the page */
    function applyTranslations() {
        const lang = getCurrentLang();
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (dict[key]) {
                el.textContent = dict[key][lang] || dict[key]['en'];
            }
        });
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (dict[key]) {
                el.placeholder = dict[key][lang] || dict[key]['en'];
            }
        });
        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            if (dict[key]) {
                el.title = dict[key][lang] || dict[key]['en'];
            }
        });
        document.querySelectorAll('[data-i18n-rows]').forEach(el => {
            const val = el.getAttribute('data-i18n-rows');
            el.text = `${val} ${t('rows')}`;
        });
    }

    /** Set language and apply RTL/LTR */
    function setLanguage(lang) {
        localStorage.setItem(STORAGE_KEY, lang);
        const html = document.documentElement;
        html.setAttribute('lang', lang);
        html.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
        applyTranslations();
        updateToggleButton(lang);
    }

    /** Create/update the language toggle button */
    function updateToggleButton(lang) {
        let btn = document.getElementById('dw-lang-toggle');
        if (btn) {
            btn.innerHTML = lang === 'ar'
                ? '<i class="fas fa-globe"></i> En'
                : '<i class="fas fa-globe"></i> Ar';
        }
    }

    /** Inject the toggle button into the navbar */
    function injectToggleButton() {
        // Find the nav-buttons container or create one
        let navBtns = document.querySelector('.nav-buttons');
        let navActions = document.querySelector('.nav-actions');
        const target = navBtns || navActions;

        if (!target) return;

        const lang = getCurrentLang();
        const btn = document.createElement('button');
        btn.id = 'dw-lang-toggle';
        btn.className = 'lang-toggle';
        btn.innerHTML = lang === 'ar'
            ? '<i class="fas fa-globe"></i> En'
            : '<i class="fas fa-globe"></i> Ar';
        btn.addEventListener('click', () => {
            const newLang = getCurrentLang() === 'en' ? 'ar' : 'en';
            setLanguage(newLang);
            window.dispatchEvent(new CustomEvent('dw-lang-changed', { detail: { lang: newLang } }));
        });

        // Insert as first child
        target.insertBefore(btn, target.firstChild);
    }

    // ═══════════════════════════════════════════════════
    //  Initialize on DOM Ready
    // ═══════════════════════════════════════════════════
    function initI18n() {
        const lang = getCurrentLang();
        const html = document.documentElement;
        html.setAttribute('lang', lang);
        html.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
        injectToggleButton();
        applyTranslations();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initI18n);
    } else {
        initI18n();
    }

    // ═══════════════════════════════════════════════════
    //  Expose globally
    // ═══════════════════════════════════════════════════
    window.t = t;
    window.getCurrentLang = getCurrentLang;
    window.setLanguage = setLanguage;
    window.applyTranslations = applyTranslations;

})();
