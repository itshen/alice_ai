"""
XML解析器 - 用于解析AI输出中的工具调用
"""
import re
import json
from typing import List, Dict, Any, Optional

class XMLParser:
    """XML解析器"""
    
    @staticmethod
    def extract_tool_calls(text: str) -> List[Dict[str, Any]]:
        """从文本中提取工具调用"""
        tool_calls = []
        
        # 匹配 <tool_calls>...</tool_calls> 格式
        pattern = r'<tool_calls>(.*?)</tool_calls>'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                # 尝试解析JSON
                tool_call_data = json.loads(match.strip())
                if isinstance(tool_call_data, list):
                    # 过滤并验证每个工具调用
                    for call in tool_call_data:
                        if XMLParser._validate_tool_call(call):
                            tool_calls.append(call)
                        else:
                            print(f"⚠️ 跳过无效的工具调用: {call}")
                else:
                    if XMLParser._validate_tool_call(tool_call_data):
                        tool_calls.append(tool_call_data)
                    else:
                        print(f"⚠️ 跳过无效的工具调用: {tool_call_data}")
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON解析失败: {e}")
                print(f"原始内容: {match.strip()[:200]}...")
                # 如果不是JSON，尝试解析XML格式
                xml_calls = XMLParser._parse_xml_tool_calls(match)
                for call in xml_calls:
                    if XMLParser._validate_tool_call(call):
                        tool_calls.append(call)
                    else:
                        print(f"⚠️ 跳过无效的XML工具调用: {call}")
        
        # 也支持直接的XML格式工具调用
        xml_pattern = r'<tool_call[^>]*>(.*?)</tool_call>'
        xml_matches = re.findall(xml_pattern, text, re.DOTALL)
        
        for match in xml_matches:
            tool_call = XMLParser._parse_single_xml_tool_call(match)
            if tool_call and XMLParser._validate_tool_call(tool_call):
                tool_calls.append(tool_call)
            elif tool_call:
                print(f"⚠️ 跳过无效的单个工具调用: {tool_call}")
        
        # 检查工具调用数量约束：每次只能调用一个工具
        if len(tool_calls) > 1:
            print(f"❌ 检测到 {len(tool_calls)} 个工具调用，违反约束！每次只能调用一个工具")
            print("⚠️ 只保留第一个工具调用，忽略其余调用")
            tool_calls = tool_calls[:1]
        
        return tool_calls
    
    @staticmethod
    def _validate_tool_call(tool_call: Dict[str, Any]) -> bool:
        """验证工具调用格式"""
        try:
            # 检查基本结构
            if not isinstance(tool_call, dict):
                return False
            
            # 检查是否有function字段
            if "function" not in tool_call:
                return False
            
            function = tool_call["function"]
            if not isinstance(function, dict):
                return False
            
            # 检查必需字段 - 只要有name就行
            if "name" not in function or not function["name"]:
                return False
            
            # 对于arguments字段，更宽松的检查
            if "arguments" in function:
                args = function["arguments"]
                if isinstance(args, str):
                    # 如果是空字符串，也是有效的
                    if args.strip() == "":
                        return True
                    # 尝试解析JSON参数
                    try:
                        json.loads(args)
                    except json.JSONDecodeError:
                        print(f"⚠️ 参数JSON格式无效: {args}")
                        return False
                elif args is None:
                    # None也是有效的
                    return True
                elif not isinstance(args, dict):
                    # 其他类型暂时不接受
                    return False
            
            return True
        except Exception as e:
            print(f"⚠️ 验证工具调用时出错: {e}")
            return False
    
    @staticmethod
    def _parse_xml_tool_calls(xml_text: str) -> List[Dict[str, Any]]:
        """解析XML格式的工具调用"""
        tool_calls = []
        
        # 匹配单个工具调用
        pattern = r'<tool_call[^>]*>(.*?)</tool_call>'
        matches = re.findall(pattern, xml_text, re.DOTALL)
        
        for match in matches:
            tool_call = XMLParser._parse_single_xml_tool_call(match)
            if tool_call:
                tool_calls.append(tool_call)
        
        return tool_calls
    
    @staticmethod
    def _parse_single_xml_tool_call(xml_content: str) -> Optional[Dict[str, Any]]:
        """解析单个XML工具调用"""
        try:
            # 提取工具名称
            name_match = re.search(r'<name>(.*?)</name>', xml_content, re.DOTALL)
            
            if not name_match:
                return None
            
            tool_name = name_match.group(1).strip()
            
            # 提取参数
            params_match = re.search(r'<parameters>(.*?)</parameters>', xml_content, re.DOTALL)
            if not params_match:
                params_match = re.search(r'<parameter>(.*?)</parameter>', xml_content, re.DOTALL)
            parameters = {}
            
            if params_match:
                params_content = params_match.group(1).strip()
                
                # 尝试解析JSON参数
                try:
                    parameters = json.loads(params_content)
                except json.JSONDecodeError:
                    # 如果不是JSON，尝试解析XML参数
                    parameters = XMLParser._parse_xml_parameters(params_content)
            
            return {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "arguments": json.dumps(parameters, ensure_ascii=False)
                }
            }
        
        except Exception as e:
            return None
    
    @staticmethod
    def _parse_xml_parameters(xml_content: str) -> Dict[str, Any]:
        """解析XML格式的参数"""
        parameters = {}
        
        # 匹配所有参数标签
        param_pattern = r'<(\w+)>(.*?)</\1>'
        matches = re.findall(param_pattern, xml_content, re.DOTALL)
        
        for param_name, param_value in matches:
            param_value = param_value.strip()
            
            # 尝试转换数据类型
            if param_value.lower() in ('true', 'false'):
                parameters[param_name] = param_value.lower() == 'true'
            elif param_value.isdigit():
                parameters[param_name] = int(param_value)
            elif re.match(r'^\d+\.\d+$', param_value):
                parameters[param_name] = float(param_value)
            else:
                parameters[param_name] = param_value
        
        return parameters
    
    @staticmethod
    def remove_tool_calls(text: str) -> str:
        """从文本中移除工具调用标记"""
        # 移除 <tool_calls>...</tool_calls>
        text = re.sub(r'<tool_calls>.*?</tool_calls>', '', text, flags=re.DOTALL)
        
        # 移除 <tool_call>...</tool_call>
        text = re.sub(r'<tool_call[^>]*>.*?</tool_call>', '', text, flags=re.DOTALL)
        
        return text.strip()
    
    @staticmethod
    def has_tool_calls(text: str) -> bool:
        """检查文本是否包含工具调用"""
        return bool(re.search(r'<tool_calls>|<tool_call[^>]*>', text))



# 全局解析器实例
xml_parser = XMLParser() 