# 网络漫画整合器

一个简单易用的工具，用于将漫画图片整合成PDF文件。

## 功能特点

- 支持多种图片格式（PNG, JPG, JPEG, WEBP, GIF, BMP）
- 自动按照文件名中的数字排序
- 支持从ZIP文件中提取图片
- 支持批量处理多个文件夹或ZIP文件
- 支持合并多个PDF文件
- 友好的图形用户界面
- 实时进度显示

## 使用要求

运行前需要安装以下Python包：
```
pip install pillow
pip install tkinter (Python 3.x 通常已预装)
pip install PyPDF2
```

## 使用方法

1. 运行程序 `python img_2_pdf_2.py`
2. 选择操作模式：
   - 单个文件夹模式：将一个文件夹中的所有图片合并为PDF
   - ZIP文件模式：从ZIP文件中提取图片并合并为PDF
   - 批量ZIP模式：批量处理多个ZIP文件
   - 批量文件夹模式：批量处理多个文件夹
   - 合并PDF模式：将多个PDF文件合并为一个

## 开发者

hal3000-t2025 