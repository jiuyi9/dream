# -*- coding: utf-8 -*-

import keyring

# keyring 中的 service 名
SERVICE_NAME = "aicode-auth"


class CredentialInputCancelled(Exception):
    """用户在凭据输入弹窗中取消。"""


def get_valid_credentials(verify=None):
    """返回 (username, password)，保证有效。唯一的凭据获取入口。

    统一流程：
    ① 无已存凭据 → 弹窗输入 → verify 验证 → 通过则存入返回，失败窗内一直改到通过或取消
    ② 有已存凭据 → verify 验证 → 通过直接返回；失败则清旧凭据走①弹窗重输

    verify: (username, password) -> None|str。None 通过/str 失败提示。
            为 None 时不验证，有已存凭据直接返回。
    """
    username, password = _read()
    if username and password and (verify is None or verify(username, password) is None):
        return username, password
    # 无凭据 或 已存凭据验证失败 → 清旧弹窗重输（窗内 verify 闭环）
    _delete()
    return _prompt_and_store(verify)


def _read():
    """读已存凭据，返回 (username, password)，无则空串。"""
    cred = keyring.get_credential(SERVICE_NAME, None)
    if not cred:
        return "", ""
    return cred.username, cred.password


def _store(username, password):
    """一条写入：账号进 UserName 字段，密码进密码字段。"""
    keyring.set_password(SERVICE_NAME, username, password)


def _delete():
    """删除已存凭据，无则忽略。"""
    cred = keyring.get_credential(SERVICE_NAME, None)
    if not cred:
        return
    try:
        keyring.delete_password(SERVICE_NAME, cred.username)
    except Exception:
        pass


def _prompt_and_store(verify=None):
    """弹窗引导输入并存储。verify 通过才存储返回；取消抛 CredentialInputCancelled。"""
    username, password = _gui_prompt(verify)
    _store(username, password)
    return username, password


# 图形界面（tkinter，标准库零依赖）

def _gui_prompt(verify=None):
    """弹窗输入账号密码。

    点确定：空值则窗内提示；verify 为 None 直接通过；verify 通过则关窗返回，
    失败则窗内显示固定错误信息、不关窗、不清空输入，可一直改到通过。
    点取消/ESC：抛 CredentialInputCancelled。
    密码框带小眼睛切换显示/隐藏。

    如果已有 Tk 实例（如被 build_gui 调用），则使用 Toplevel 避免双 Tk 冲突。
    """
    import tkinter as tk
    from tkinter import ttk
    import time

    result = {"username": "", "password": "", "done": False}

    existing_root = _get_existing_tk_root()

    if existing_root is not None:
        root = tk.Toplevel(existing_root)
        root.transient(existing_root)
        root.grab_set()
    else:
        root = tk.Tk()
    root.title("凭据配置")
    root.resizable(False, False)
    root.protocol("WM_DELETE_WINDOW", root.destroy)

    # 居中显示
    root.update_idletasks()
    width, height = 420, 260
    x = (root.winfo_screenwidth() - width) // 2
    y = (root.winfo_screenheight() - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")

    tk.Label(root, text="请输入用户名和密码\n凭据将加密保存到系统凭据管理器",
             justify="center", pady=12).pack(fill="x")

    form = tk.Frame(root, padx=24)
    form.pack(fill="x")

    tk.Label(form, text="账号:").grid(row=0, column=0, sticky="e", pady=6)
    username_var = tk.StringVar()
    username_entry = ttk.Entry(form, textvariable=username_var)
    username_entry.grid(row=0, column=1, sticky="ew", pady=6, padx=(8, 0))

    tk.Label(form, text="密码:").grid(row=1, column=0, sticky="e", pady=6)
    password_var = tk.StringVar()
    password_entry = ttk.Entry(form, textvariable=password_var, show="*")
    password_entry.grid(row=1, column=1, sticky="ew", pady=6, padx=(8, 0))

    def toggle_password():
        if password_entry.cget("show") == "*":
            password_entry.config(show="")
            eye_button.config(text="🙈")
        else:
            password_entry.config(show="*")
            eye_button.config(text="👁")

    eye_button = tk.Button(form, text="👁", command=toggle_password, bd=0)
    eye_button.grid(row=1, column=2, pady=6, padx=(4, 0))
    form.columnconfigure(1, weight=1)

    error_var = tk.StringVar()
    tk.Label(root, textvariable=error_var, fg="red", pady=4).pack(fill="x")

    btn_frame = tk.Frame(root, pady=12)
    btn_frame.pack(fill="x")

    def on_ok():
        u = username_var.get().strip()
        p = password_var.get()
        if not u or not p:
            error_var.set("请输入账号和密码")
            return
        if verify is not None:
            try:
                err = verify(u, p)
            except Exception as e:
                err = f"验证异常：{type(e).__name__}"
            if err:
                error_var.set(err)
                root.update_idletasks()
                return
        result["username"] = u
        result["password"] = p
        result["done"] = True
        root.destroy()

    def on_cancel():
        root.destroy()

    tk.Button(btn_frame, text="取消", width=8, command=on_cancel).pack(side="right", padx=(8, 24))
    tk.Button(btn_frame, text="确定", width=8, command=on_ok).pack(side="right")

    root.bind("<Return>", lambda e: on_ok())
    root.bind("<Escape>", lambda e: on_cancel())
    username_entry.focus_set()

    if existing_root is not None:
        # Toplevel 模式：用 update() 轮询，最可靠
        while not result["done"]:
            try:
                root.update()
                root.update_idletasks()
            except tk.TclError:
                break
            time.sleep(0.03)
    else:
        root.mainloop()

    if not result["done"]:
        raise CredentialInputCancelled()
    return result["username"], result["password"]


def _get_existing_tk_root():
    """返回已有的 Tk 根窗口实例，没有则返回 None。"""
    import tkinter as tk
    try:
        root = getattr(tk, '_default_root', None)
        if root is not None:
            return root
    except Exception:
        pass
    return None
