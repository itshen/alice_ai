#!/usr/bin/env python3.11
"""
AI Chat Tools 安装脚本
"""
from setuptools import setup, find_packages

with open("ai_chat_tools/README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("ai_chat_tools/requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ai-chat-tools",
    version="1.0.0",
    author="AI Chat Tools",
    author_email="",
    description="简化的AI工具调用框架，支持多模型、工具调用、SQLite持久化",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/itshen/ai-chat-tools",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ai-chat-tools=ai_chat_tools.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "ai_chat_tools": ["*.md", "*.txt"],
    },
) 