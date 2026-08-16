# -*- coding: utf-8 -*-
"""demo_seed.py — 桌面示例附加：内置演示账号

上游 OpenHarvey 没有种子数据，首次启动数据库为空，用户只能先注册才能进入。
桌面示例要求「双击即跑」，因此在启动时幂等地写入一个演示管理员账号。

口令可用环境变量覆盖：
    FASTLEGAL_ADMIN_EMAIL / FASTLEGAL_ADMIN_PASSWORD
"""
import os

import bcrypt

from db import SessionLocal, User, UserProfile, init_db

DEMO_EMAIL = os.getenv("FASTLEGAL_ADMIN_EMAIL", "admin@fastlegal.example")
DEMO_PASSWORD = os.getenv("FASTLEGAL_ADMIN_PASSWORD", "FastLegal2026$")


def ensure_demo_user(email: str | None = None, password: str | None = None) -> tuple[str, str]:
    """建表 + 幂等写入演示账号，返回 (email, password)。"""
    email = email or DEMO_EMAIL
    password = password or DEMO_PASSWORD

    init_db()
    db = SessionLocal()
    try:
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(
                email=email,
                password_hash=pw_hash,
                display_name="Demo Admin",
                organisation="FastLegal Demo",
            )
            db.add(user)
            db.flush()
            db.add(UserProfile(user_id=user.id))
        else:
            # 口令始终对齐当前配置，避免改过环境变量后旧哈希导致登录失败
            user.password_hash = pw_hash
        db.commit()
    finally:
        db.close()
    return email, password


if __name__ == "__main__":
    print("[OK] demo account:", " / ".join(ensure_demo_user()))
