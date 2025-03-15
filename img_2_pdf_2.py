#这是一个把漫画图片整合成PDF的小工具
# 1. 读取指定目录下的所有图片
# 2. 按照文件名排序
# 3. 把图片合并成一个PDF文件
# 4. 保存到指定目录
#
# 运行前需要安装以下包：
# pip install pillow
# pip install tkinter (Python 3.x 通常已预装)
# pip install PyPDF2


import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import os
import re
import zipfile
import tempfile
import shutil
import threading
from PyPDF2 import PdfMerger

# 提取文件名中的数字
def extract_number(filename):
    numbers = re.findall(r'\d+', filename)
    return int(numbers[0]) if numbers else 0

# 检查文件是否为图片
def is_image_file(filename):
    return filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'))

# 从ZIP文件中提取图片
def extract_images_from_zip(zip_file, progress_callback=None):
    temp_dir = tempfile.mkdtemp()
    
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            # 获取所有文件列表
            file_list = zip_ref.namelist()
            
            # 检查是否包含图片文件
            has_images = any(is_image_file(file) for file in file_list)
            
            if not has_images:
                shutil.rmtree(temp_dir)
                return None
            
            # 提取所有文件到临时目录
            if progress_callback:
                progress_callback(0, f"正在提取ZIP文件: {os.path.basename(zip_file)}")
            
            total_files = len(file_list)
            for i, file in enumerate(file_list):
                zip_ref.extract(file, temp_dir)
                if progress_callback and i % max(1, total_files // 10) == 0:  # 每10%更新一次
                    progress = (i + 1) / total_files * 100
                    progress_callback(progress, f"正在提取文件: {i+1}/{total_files}")
            
            if progress_callback:
                progress_callback(100, "ZIP文件提取完成")
            
            return temp_dir
    except Exception as e:
        if progress_callback:
            progress_callback(100, f"提取失败: {str(e)}")
        shutil.rmtree(temp_dir)
        return None

# 创建进度条窗口
def create_progress_window(parent, title="处理中"):
    progress_window = tk.Toplevel(parent)
    progress_window.title(title)
    progress_window.geometry("400x150")
    progress_window.resizable(False, False)
    progress_window.transient(parent)  # 设置为父窗口的临时窗口
    progress_window.grab_set()  # 模态窗口
    
    # 居中显示
    parent_x = parent.winfo_x()
    parent_y = parent.winfo_y()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()
    
    x = parent_x + (parent_width - 400) // 2
    y = parent_y + (parent_height - 150) // 2
    
    progress_window.geometry(f"+{x}+{y}")
    
    # 添加进度条
    frame = tk.Frame(progress_window, padx=20, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    status_label = tk.Label(frame, text="准备中...", anchor="w")
    status_label.pack(fill=tk.X, pady=(0, 10))
    
    progress = ttk.Progressbar(frame, orient="horizontal", length=360, mode="determinate")
    progress.pack(fill=tk.X, pady=(0, 10))
    
    percent_label = tk.Label(frame, text="0%")
    percent_label.pack()
    
    # 防止关闭按钮
    progress_window.protocol("WM_DELETE_WINDOW", lambda: None)
    
    return progress_window, progress, status_label, percent_label

# 将图片合并成PDF
def images_to_pdf(image_folder, output_pdf, is_temp_dir=False, progress_callback=None):
    try:
        # 获取所有图片文件
        if os.path.isdir(image_folder):
            if progress_callback:
                progress_callback(0, f"正在扫描图片文件...")
            
            image_files = [f for f in os.listdir(image_folder) if is_image_file(f)]
            
            if not image_files:
                if progress_callback:
                    progress_callback(100, "没有找到图片文件")
                return False
            
            if progress_callback:
                progress_callback(10, f"找到 {len(image_files)} 个图片文件，正在排序...")
            
            sorted_files = sorted(image_files, key=extract_number)
            
            if progress_callback:
                progress_callback(20, "正在加载图片...")
            
            images = []
            total_files = len(sorted_files)
            
            for i, img_file in enumerate(sorted_files):
                img_path = os.path.join(image_folder, img_file)
                images.append(Image.open(img_path).convert('RGB'))
                
                if progress_callback:
                    progress = 20 + (i + 1) / total_files * 60  # 从20%到80%
                    progress_callback(progress, f"正在处理图片: {i+1}/{total_files}")
        else:
            # 如果是ZIP文件
            if progress_callback:
                progress_callback(0, f"正在处理ZIP文件: {os.path.basename(image_folder)}")
            
            temp_dir = extract_images_from_zip(image_folder, 
                                             lambda p, s: progress_callback(p * 0.5, s) if progress_callback else None)
            
            if temp_dir:
                # 递归调用自身，但使用提取的临时目录
                if progress_callback:
                    progress_callback(50, "ZIP提取完成，开始处理图片...")
                
                # 为递归调用创建一个进度回调函数，将50%-100%映射到原始的50%-100%
                def nested_callback(p, s):
                    if progress_callback:
                        mapped_progress = 50 + p * 0.5
                        progress_callback(mapped_progress, s)
                
                result = images_to_pdf(temp_dir, output_pdf, True, nested_callback)
                # 清理临时目录
                shutil.rmtree(temp_dir)
                return result
            else:
                if progress_callback:
                    progress_callback(100, "ZIP文件中没有找到图片")
                return False
        
        if images:
            if progress_callback:
                progress_callback(80, "正在生成PDF文件...")
            
            images[0].save(output_pdf, save_all=True, append_images=images[1:])
            
            if progress_callback:
                progress_callback(100, f"PDF创建成功: {os.path.basename(output_pdf)}")
            
            print(f"PDF created successfully: {output_pdf}")
            return True
        else:
            if progress_callback:
                progress_callback(100, "没有找到图片文件")
            
            print("No images found in the folder.")
            return False
    except Exception as e:
        if progress_callback:
            progress_callback(100, f"错误: {str(e)}")
        
        print(f"Error creating PDF: {e}")
        return False
    finally:
        # 如果是临时目录且函数是被递归调用的，不在这里删除
        # 让调用者负责删除临时目录
        pass

# 合并多个PDF文件
def merge_pdfs(pdf_files, output_pdf, progress_callback=None):
    try:
        merger = PdfMerger()
        
        total_files = len(pdf_files)
        for i, pdf in enumerate(pdf_files):
            if progress_callback:
                progress = (i / total_files) * 90  # 保留最后10%用于写入文件
                progress_callback(progress, f"正在合并PDF: {i+1}/{total_files}")
            
            merger.append(pdf)
        
        if progress_callback:
            progress_callback(90, "正在写入合并后的PDF文件...")
        
        merger.write(output_pdf)
        merger.close()
        
        if progress_callback:
            progress_callback(100, f"PDF合并成功: {os.path.basename(output_pdf)}")
        
        print(f"PDFs merged successfully: {output_pdf}")
        return True
    except Exception as e:
        if progress_callback:
            progress_callback(100, f"合并失败: {str(e)}")
        
        print(f"Error merging PDFs: {e}")
        return False

# 在后台线程中执行任务
def run_in_thread(root, func, args=(), on_complete=None):
    progress_window, progress_bar, status_label, percent_label = create_progress_window(root)
    
    def update_progress(value, status_text):
        # 在主线程中更新UI
        root.after(0, lambda: progress_bar.configure(value=value))
        root.after(0, lambda: status_label.configure(text=status_text))
        root.after(0, lambda: percent_label.configure(text=f"{int(value)}%"))
    
    def thread_func():
        result = func(*args, progress_callback=update_progress)
        
        # 任务完成后在主线程中执行回调
        if on_complete:
            root.after(1000, lambda: on_complete(result))  # 延迟1秒关闭进度窗口
    
    # 启动线程
    thread = threading.Thread(target=thread_func)
    thread.daemon = True
    thread.start()
    
    return progress_window

# 单文件夹模式
def single_folder_mode():
    folder_selected = filedialog.askdirectory(title="选择包含图片的文件夹")
    if folder_selected:
        output_pdf = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if output_pdf:
            progress_window = run_in_thread(
                root,
                images_to_pdf,
                args=(folder_selected, output_pdf),
                on_complete=lambda result: complete_task(progress_window, result, 
                                                      success_msg=f"PDF创建成功: {os.path.basename(output_pdf)}",
                                                      error_msg="创建PDF失败，文件夹中没有找到图片文件")
            )

# ZIP文件模式
def zip_file_mode():
    zip_file = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
    if zip_file:
        output_pdf = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if output_pdf:
            progress_window = run_in_thread(
                root,
                images_to_pdf,
                args=(zip_file, output_pdf),
                on_complete=lambda result: complete_task(progress_window, result,
                                                      success_msg=f"ZIP文件中的图片已成功转换为PDF: {os.path.basename(output_pdf)}",
                                                      error_msg="ZIP文件中没有找到图片文件")
            )

# ZIP批量模式
def batch_zip_mode():
    zip_files = filedialog.askopenfilenames(title="选择多个ZIP文件", filetypes=[("ZIP files", "*.zip")])
    if zip_files:
        output_folder = filedialog.askdirectory(title="选择PDF输出文件夹")
        if output_folder:
            # 创建一个处理所有ZIP文件的函数
            def process_all_zips(progress_callback=None):
                success_count = 0
                fail_count = 0
                total_files = len(zip_files)
                
                for i, zip_file in enumerate(zip_files):
                    # 更新总体进度
                    if progress_callback:
                        overall_progress = (i / total_files) * 100
                        progress_callback(overall_progress, f"处理ZIP文件 {i+1}/{total_files}: {os.path.basename(zip_file)}")
                    
                    # 获取ZIP文件名（不含路径和扩展名）
                    zip_basename = os.path.basename(zip_file)
                    zip_name = os.path.splitext(zip_basename)[0]
                    
                    # 设置输出PDF路径
                    output_pdf = os.path.join(output_folder, f"{zip_name}.pdf")
                    
                    # 为当前ZIP文件创建一个进度回调函数
                    def zip_progress_callback(p, s):
                        if progress_callback:
                            # 计算当前ZIP在整体中的进度比例
                            file_progress_portion = 1 / total_files
                            # 当前文件的基础进度百分比
                            base_progress = (i / total_files) * 100
                            # 当前文件贡献的进度百分比
                            file_progress = p * file_progress_portion
                            # 总进度
                            overall_progress = base_progress + file_progress
                            progress_callback(overall_progress, f"[{i+1}/{total_files}] {s}")
                    
                    # 处理ZIP文件
                    if images_to_pdf(zip_file, output_pdf, progress_callback=zip_progress_callback):
                        success_count += 1
                    else:
                        fail_count += 1
                
                if progress_callback:
                    progress_callback(100, f"处理完成: 成功 {success_count} 个, 失败 {fail_count} 个")
                
                return (success_count, fail_count)
            
            # 在后台线程中处理所有ZIP文件
            progress_window = run_in_thread(
                root,
                process_all_zips,
                on_complete=lambda result: complete_batch_task(progress_window, result, output_folder)
            )

# 批量模式
def batch_mode():
    root_folder = filedialog.askdirectory(title="选择包含多个漫画文件夹的主文件夹")
    if root_folder:
        output_folder = os.path.join(root_folder, "PDF输出")
        os.makedirs(output_folder, exist_ok=True)
        
        # 创建一个处理所有文件夹的函数
        def process_all_folders(progress_callback=None):
            subdirs = [d for d in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, d))]
            total_dirs = len(subdirs)
            
            if total_dirs == 0:
                if progress_callback:
                    progress_callback(100, "没有找到子文件夹")
                return (0, 0)
            
            success_count = 0
            fail_count = 0
            
            for i, subdir in enumerate(subdirs):
                # 更新总体进度
                if progress_callback:
                    overall_progress = (i / total_dirs) * 100
                    progress_callback(overall_progress, f"处理文件夹 {i+1}/{total_dirs}: {subdir}")
                
                subdir_path = os.path.join(root_folder, subdir)
                output_pdf = os.path.join(output_folder, f"{subdir}.pdf")
                
                # 为当前文件夹创建一个进度回调函数
                def folder_progress_callback(p, s):
                    if progress_callback:
                        # 计算当前文件夹在整体中的进度比例
                        folder_progress_portion = 1 / total_dirs
                        # 当前文件夹的基础进度百分比
                        base_progress = (i / total_dirs) * 100
                        # 当前文件夹贡献的进度百分比
                        folder_progress = p * folder_progress_portion
                        # 总进度
                        overall_progress = base_progress + folder_progress
                        progress_callback(overall_progress, f"[{i+1}/{total_dirs}] {s}")
                
                if images_to_pdf(subdir_path, output_pdf, progress_callback=folder_progress_callback):
                    success_count += 1
                else:
                    fail_count += 1
            
            if progress_callback:
                progress_callback(100, f"处理完成: 成功 {success_count} 个, 失败 {fail_count} 个")
            
            return (success_count, fail_count)
        
        # 在后台线程中处理所有文件夹
        progress_window = run_in_thread(
            root,
            process_all_folders,
            on_complete=lambda result: complete_batch_task(progress_window, result, output_folder)
        )

# PDF合并模式
def merge_pdfs_mode():
    pdf_files = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
    if pdf_files:
        output_pdf = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if output_pdf:
            progress_window = run_in_thread(
                root,
                merge_pdfs,
                args=(pdf_files, output_pdf),
                on_complete=lambda result: complete_task(progress_window, result,
                                                      success_msg=f"PDF合并成功: {os.path.basename(output_pdf)}",
                                                      error_msg="PDF合并失败")
            )

# 任务完成后的处理
def complete_task(progress_window, result, success_msg, error_msg):
    progress_window.destroy()
    if result:
        messagebox.showinfo("成功", success_msg)
    else:
        messagebox.showerror("错误", error_msg)

# 批量任务完成后的处理
def complete_batch_task(progress_window, result, output_folder):
    progress_window.destroy()
    success_count, fail_count = result
    if success_count > 0:
        messagebox.showinfo("成功", f"成功创建 {success_count} 个PDF文件在: {output_folder}" + 
                          (f"\n{fail_count} 个处理失败" if fail_count > 0 else ""))
    else:
        messagebox.showerror("错误", "没有成功处理任何文件")

# 创建GUI
def create_gui():
    global root
    root = tk.Tk()
    root.title("漫画图片整合成PDF工具【老谢专用】")
    root.geometry("700x750")  # 增加窗口大小以适应新按钮
    root.configure(bg='#f0f0f0')  # 设置背景色
    
    # 创建说明文本
    instructions = """
使用说明：

1. 单文件夹模式：
   - 选择包含图片的单个文件夹
   - 选择PDF保存位置
   - 程序将按照文件名数字顺序合并图片
   - 生成单个PDF文件

2. ZIP文件模式：
   - 选择包含图片的单个ZIP文件
   - 选择PDF保存位置
   - 程序将提取ZIP中的图片并按文件名数字顺序合并
   - 生成单个PDF文件

3. ZIP批量模式：
   - 选择多个ZIP文件
   - 选择PDF输出文件夹
   - 程序将处理每个ZIP文件并生成对应的PDF
   - 每个ZIP生成一个同名PDF文件

4. 批量模式：
   - 选择包含多个漫画文件夹的主文件夹
   - 程序会在主文件夹下创建"PDF输出"文件夹
   - 自动处理所有子文件夹中的图片
   - 每个子文件夹生成一个对应的PDF文件

5. PDF合并模式：
   - 选择多个PDF文件
   - 选择合并后的PDF保存位置
   - 程序将按选择顺序合并PDF文件

注意事项：
- 支持的图片格式：PNG、JPG、JPEG、WEBP、GIF、BMP
- 图片会按文件名中的数字顺序排序
- 请确保文件名中包含数字序号
- ZIP文件必须直接包含图片文件，不支持嵌套文件夹
- 所有操作都会显示进度条，方便跟踪处理进度

版本：2
作者：hal3000
日期：2025-03-15
    """
    
    # 创建Frame来组织布局
    frame = tk.Frame(root, bg='#f0f0f0')
    frame.pack(expand=True, fill='both', padx=30, pady=30)  # 增加边距
    
    # 添加标题
    title = tk.Label(frame, 
                    text="漫画图片整合成PDF工具", 
                    font=('Arial', 18, 'bold'),  # 增大字号
                    bg='#f0f0f0')
    title.pack(pady=(0, 25))
    
    # 添加说明文本
    instruction_text = tk.Text(frame, 
                             height=28,  # 增加文本框高度
                             width=60,   # 增加文本框宽度
                             wrap=tk.WORD,
                             font=('Arial', 11),  # 略微增大字号
                             bg='#ffffff',
                             relief=tk.GROOVE)
    instruction_text.insert('1.0', instructions)
    instruction_text.config(state='disabled')  # 设置为只读
    instruction_text.pack(pady=(0, 25))  # 增加底部间距
    
    # 创建按钮框架
    button_frame = tk.Frame(frame, bg='#f0f0f0')
    button_frame.pack()
    
    # 设计按钮样式
    button_style = {
        'width': 20,
        'height': 2,
        'font': ('Arial', 11),  # 略微增大字号
        'relief': tk.RAISED,
        'cursor': 'hand2'
    }
    
    # 第一行按钮
    first_row_frame = tk.Frame(button_frame, bg='#f0f0f0')
    first_row_frame.pack(pady=(0, 15))
    
    single_button = tk.Button(first_row_frame, 
                            text="单文件夹模式",
                            command=single_folder_mode,
                            bg='#4CAF50',
                            fg='black',  # 改为黑色文字
                            **button_style)
    single_button.pack(side=tk.LEFT, padx=15)  # 增加按钮间距
    
    zip_button = tk.Button(first_row_frame, 
                         text="ZIP文件模式",
                         command=zip_file_mode,
                         bg='#9C27B0',  # 紫色
                         fg='black',
                         **button_style)
    zip_button.pack(side=tk.LEFT, padx=15)
    
    # 第二行按钮
    second_row_frame = tk.Frame(button_frame, bg='#f0f0f0')
    second_row_frame.pack(pady=(0, 15))
    
    batch_zip_button = tk.Button(second_row_frame, 
                               text="ZIP批量模式",
                               command=batch_zip_mode,
                               bg='#E91E63',  # 粉红色
                               fg='black',
                               **button_style)
    batch_zip_button.pack(side=tk.LEFT, padx=15)
    
    batch_button = tk.Button(second_row_frame,
                           text="批量模式",
                           command=batch_mode,
                           bg='#2196F3',
                           fg='black',  # 改为黑色文字
                           **button_style)
    batch_button.pack(side=tk.LEFT, padx=15)  # 增加按钮间距
    
    # 第三行按钮
    third_row_frame = tk.Frame(button_frame, bg='#f0f0f0')
    third_row_frame.pack()
    
    # 添加PDF合并按钮
    merge_button = tk.Button(third_row_frame,
                           text="PDF合并模式",
                           command=merge_pdfs_mode,
                           bg='#FF9800',
                           fg='black',
                           **button_style)
    merge_button.pack()
    
    root.mainloop()

# 运行GUI
create_gui()
