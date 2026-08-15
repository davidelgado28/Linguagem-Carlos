import sys
import os
import subprocess

def transpile_carlos_to_cpp(source_code):
    lines = source_code.split('\n')
    cpp_lines = []
    
    # Pilha para rastrear a indentação e fechar blocos { } automaticamente em C++
    indent_stack = [0]
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            cpp_lines.append(line)
            continue
            
        # Calcula o nível de indentação atual
        indent_len = len(line) - len(line.lstrip())
        
        # Fecha blocos C++ quando a indentação recua
        while len(indent_stack) > 1 and indent_len <= indent_stack[-1]:
            indent_stack.pop()
            parent_indent = " " * indent_stack[-1]
            cpp_lines.append(parent_indent + "}")

        # Isola o comentário para preservar a codificação e a sintaxe
        comment_idx = stripped.find('//')
        if comment_idx != -1:
            code_part = stripped[:comment_idx].strip()
            comment_part = ' ' + stripped[comment_idx:]
        else:
            code_part = stripped
            comment_part = ''
            
        if not code_part:
            cpp_lines.append(line)
            continue

        is_block_starter = False
        
        # Tratamento de condicionais e laços com dois pontos (estilo Python / blocos C++)
        if code_part.startswith('elif '):
            cond = code_part[5:].strip()
            if cond.endswith(':'):
                cond = cond[:-1].strip()
            if not (cond.startswith('(') and cond.endswith(')')):
                cond = f"({cond})"
            code_part = f"else if {cond} {{"
            is_block_starter = True
        elif code_part == 'elif' or code_part == 'elif:':
            code_part = "else {"
            is_block_starter = True
        elif code_part.startswith('if '):
            cond = code_part[3:].strip()
            if cond.endswith(':'):
                cond = cond[:-1].strip()
            if not (cond.startswith('(') and cond.endswith(')')):
                cond = f"({cond})"
            code_part = f"if {cond} {{"
            is_block_starter = True
        elif code_part in ('else:', 'else'):
            code_part = "else {"
            is_block_starter = True
        elif code_part.startswith('while '):
            cond = code_part[6:].strip()
            if cond.endswith(':'):
                cond = cond[:-1].strip()
            if not (cond.startswith('(') and cond.endswith(')')):
                cond = f"({cond})"
            code_part = f"while {cond} {{"
            is_block_starter = True
        elif code_part.startswith('for '):
            header = code_part[4:].strip()
            if header.endswith(':'):
                header = header[:-1].strip()
            if not (header.startswith('(') and header.endswith(')')):
                header = f"({header})"
            code_part = f"for {header} {{"
            is_block_starter = True

        if is_block_starter:
            indent_stack.append(indent_len)
            cpp_lines.append(line[:indent_len] + code_part + comment_part)
            continue

        # Regras de inserção de ponto e vírgula
        excluded_ends = ('{', '}', ';', ',', ':', '#')
        needs_semicolon = True
        
        if code_part.endswith(excluded_ends) or code_part.startswith('#'):
            needs_semicolon = False
            
        if code_part.startswith(('using ', 'int ', 'double ', 'float ', 'string ', 'char ', 'return ', 'cin ', 'cout ')):
            needs_semicolon = True

        if needs_semicolon and not code_part.endswith(';'):
            code_part += ';'

        cpp_lines.append(line[:indent_len] + code_part + comment_part)
        
    # Fecha quaisquer blocos abertos restantes no final do arquivo
    while len(indent_stack) > 1:
        indent_stack.pop()
        cpp_lines.append("}")
        
    return '\n'.join(cpp_lines)

def main():
    if len(sys.argv) < 2:
        print("Uso: python carlosc.py <arquivo.carlos>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    if not input_file.endswith('.carlos'):
        print("Erro: O arquivo deve ter a extensão .carlos")
        sys.exit(1)
        
    output_cpp = input_file.replace('.carlos', '.cpp')
    output_bin = input_file.replace('.carlos', '')
    if os.name == 'nt':
        output_bin += '.exe'
        
    with open(input_file, 'r', encoding='utf-8') as f:
        carlos_code = f.read()
        
    cpp_code = transpile_carlos_to_cpp(carlos_code)
    
    with open(output_cpp, 'w', encoding='utf-8') as f:
        f.write(cpp_code)
        
    print(f"[carlosc] Arquivo traduzido para {output_cpp}. Compilando...")
    
    project_dir = os.path.dirname(os.path.abspath(input_file))
    if not project_dir:
        project_dir = "."
        
    compile_cmd = ['g++', output_cpp, f'-I{project_dir}', '-o', output_bin]
    result = subprocess.run(compile_cmd)
    
    if result.returncode == 0:
        print(f"[carlosc] Compilação concluída com sucesso! Executável gerado: {output_bin}")
    else:
        print("[carlosc] Erro durante a compilação do C++.")

if __name__ == '__main__':
    main()