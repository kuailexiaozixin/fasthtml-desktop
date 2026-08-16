import shutil

import dotenv

# 必须在其它 code_assistant 子模块之前导入：给厂商下拉扩充
# DeepSeek / OpenRouter / Agnes 2（详见 providers_ext.py 文件头注释）。
from code_assistant import providers_ext

from code_assistant.assistants import ManagerFactory
from code_assistant.routes import home, chat_message, code, edit, file_rt, upload, context, preview, fix_errors, \
    set_keys, update_provider
from fasthtml.common import *

from code_assistant.constants.scroll_script_src import scroll_script_src
from code_assistant.constants.css_text import css_text
from code_assistant.constants.post_message_listener_src import post_message_listener_src
from code_assistant.util.file_util import get_mount_from_project
from code_assistant.constants.config import GENERATED_APPS_DIR, USER, PASSWORD

from importlib.resources import files

dotenv.load_dotenv()

css = Style(css_text)

# Set up the app, including daisyui and tailwind for the chat component
tlink = Script(src="https://cdn.tailwindcss.com")
dlink = Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@4.11.1/dist/full.min.css")
plink = Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@latest/css/pico.min.css")
scrollScript = Script(scroll_script_src)

app_routes = []

print(f"Generated apps dir: {GENERATED_APPS_DIR}")
if not os.path.exists(GENERATED_APPS_DIR):
    print(f"Creating: {GENERATED_APPS_DIR}")
    os.makedirs(GENERATED_APPS_DIR)

    generated_apps_dir = files('code_assistant').joinpath('generated_apps')
    print(f"Copying files to : {GENERATED_APPS_DIR}")
    for file in generated_apps_dir.iterdir():
        if file.is_dir():
            shutil.copytree(file, os.path.join(GENERATED_APPS_DIR, file.name))
        elif file.is_file():
            shutil.copy(file, GENERATED_APPS_DIR)

for project in os.listdir(GENERATED_APPS_DIR):
    project_path = os.path.join(GENERATED_APPS_DIR, project)
    if os.path.isdir(project_path):
        mount = get_mount_from_project(project)
        app_routes.append(mount)

iframe_post_message_script = Script(post_message_listener_src, type="module")

# 修复：fasthtml 注入的是 htmx 2.x，默认不执行「局部刷新」返回的内联 <script>。
# 原 key_modal_page 用内联 <script> 调用 showModal() 打开弹窗，首次整页加载能碰巧打开，
# 但切换 provider（点 other）属于 htmx 局部刷新——内联脚本不执行 → 弹窗永不打开 → 页面空白。
# 实测 pywebview/WebView2 桌面壳中：MutationObserver、htmx:afterSettle/afterSwap、
# 甚至 htmx.config.allowScriptTags 都不足以稳定触发。最稳的是「定时轮询」：
# 只要 #key_modal 在 DOM 里且没打开，就反复调用 showModal()，不依赖任何事件。
# 用户提交 key 后页面会跳转到 /，#key_modal 消失，轮询自然无事发生。
modal_autoshow_script = Script("""
(function(){
  function openKeyModal(){
    var m = document.getElementById('key_modal');
    if (m && !m.open) {
      try { m.showModal(); } catch(e) {}
    }
  }
  // 立即执行一次 + 每 100ms 轮询一次；间隔短到用户无感，长到不耗性能。
  openKeyModal();
  setInterval(openKeyModal, 100);
})();
""")


middleware = []
if USER is not None and PASSWORD is not None:
    print("Setting up basic auth")
    auth = user_pwd_auth({USER: PASSWORD}, skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css'])
    middleware.append(auth)

app, rt = fast_app(hdrs=(tlink, dlink, css, scrollScript, plink, iframe_post_message_script, modal_autoshow_script), routes=app_routes, middleware=middleware)

#setup_toasts(app) work around toast bug until fasthtml 5.2 ships
app.hdrs += (Style(toast_css), Script(toast_js, type="module"))
app.after.append(toast_after)

class AppState:
    def __init__(self):
        self._manager = None
        self.messages = []

    @property
    def manager(self):
        if self._manager is None:
            self._manager = self.initialize_manager()
        return self._manager

    def initialize_manager(self):
        return ManagerFactory(app)

app.state = AppState()

app.get('/')(home.page)
app.get("/chat_message/{msg_idx}")(chat_message.page)
app.post("/code")(code.page)
app.post("/edit/{programid}")(edit.page)
app.get("/file")(file_rt.page)
app.post("/upload")(upload.page)
app.get("/context")(context.page)
app.post("/preview/{program_id}")(preview.page)
app.post('/fix_errors')(fix_errors.page)
app.post('/keys')(set_keys.page)
# 用扩展版：切换厂商时自动预填该厂商的常用模型串（上游会清空，导致用户漏改模型）
app.post('/provider')(providers_ext.provider_page)

serve()
