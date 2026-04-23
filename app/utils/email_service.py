from fastapi_mail import FastMail, MessageSchema, MessageType
from app.core.config import conf

import random

async def send_verification_otp(email_to: str, otp: str):
    html = f"""
    <div style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 400px; margin: auto; background: white; padding: 30px; border-radius: 10px; text-align: center;">
            <h2 style="color: #333;">Xác thực tài khoản DocuMind</h2>
            <p style="color: #666;">Mã xác thực của sếp là:</p>
            <div style="font-size: 32px; font-weight: bold; color: #4A90E2; letter-spacing: 5px; margin: 20px 0; padding: 10px; border: 2px dashed #4A90E2;">
                {otp}
            </div>
            <p style="font-size: 12px; color: #999;">Mã này có hiệu lực trong 10 phút. Đừng chia sẻ cho ai kẻo bị hack mất mindmap nhé!</p>
        </div>
    </div>
    """

    message = MessageSchema(
        subject="[DocuMind] Mã xác thực đăng ký",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)