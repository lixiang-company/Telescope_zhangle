import zstandard as zstd
import os,re, sys
import argparse


def find_zst_files(directory):
    zst_files = []
    for filename in os.listdir(directory):
        if filename.endswith('.zst'):
            zst_files.append(filename)
    return zst_files

# 获取当前工作目录
current_directory = os.getcwd()

# 找到所有以 .zst 结尾的文件
zst_files = find_zst_files(current_directory)

# 输出找到的文件
for fileName in zst_files:
    with open(fileName, 'rb') as compressed:
        output_file = fileName.replace('.zst', '.log')
        try:
            with open(output_file, 'wb') as decompressed:
                dctx = zstd.ZstdDecompressor()
                dctx.copy_stream(compressed, decompressed)
                print(f"Decompressed {fileName} to {output_file}")
        except FileNotFoundError:
            print(f"错误：文件 '{fileName}' 未找到。")
        except IOError:
            print(f"错误：无法读取文件 '{fileName}'。")
        except Exception as e:
            print(f"发生了一个错误：{e}")



# fileName = sys.argv[1]
# with open(fileName, 'rb') as compressed:
#     output_file = fileName.replace('.zst', '.log')
#     try:
#         with open(output_file, 'wb') as decompressed:
#             dctx = zstd.ZstdDecompressor()
#             dctx.copy_stream(compressed, decompressed)
#             print(f"Decompressed {fileName} to {output_file}")
#     except FileNotFoundError:
#         print(f"错误：文件 '{fileName}' 未找到。")
#     except IOError:
#         print(f"错误：无法读取文件 '{fileName}'。")
#     except Exception as e:
#         print(f"发生了一个错误：{e}")

# def main(fileName):
#     print(f"{fileName}")
#     with open(fileName, 'rb') as compressed:
#         output_file = fileName.replace('.zst', '.log')
#         print(output_file)
#         with open(output_file, 'wb') as decompressed:
#             dctx = zstd.ZstdDecompressor()
#             dctx.copy_stream(compressed, decompressed)

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="一个简单的示例脚本")
#     parser.add_argument("fileName", type=str, help="你的名字")
#     args = parser.parse_args()

#     print(args.fileName)
#     main(args.fileName)