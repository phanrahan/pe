import os
import subprocess

__all__ = ['harness', 'compile']

def testsource(tests):
    source = '''
    unsigned int tests[{}][{}] = {{
'''.format(len(tests), len(tests[0]))

    for test in tests:
        testvector = ', '.join([str(t) for t in test])
        source += '''\
        {{ {} }}, 
'''.format(testvector)

    source += '''\
    };
'''
    return source

def bodysource(tests):
    return '''
    for(int i = 0; i < {ntests}; i++) {{
        unsigned int* test = tests[i];
        top->op_a = test[0];
        top->op_b = test[1];
        top->eval();
        std::cout << test[0] << ", " << test[1] << ", " << test[2] << ", " << top->res << "\\n";
        //assert(top->res == test[2]);
    }}
'''.format(ntests=len(tests))

def harness(name, opcode, tests):

    test = testsource(tests)
    body = bodysource(tests)
    return '''\
#include "V{name}.h"
#include "verilated.h"
#include <cassert>
#include <iostream>

int main(int argc, char **argv, char **env) {{
    Verilated::commandArgs(argc, argv);
    V{name}* top = new V{name};

    {test}

    top->op_code = {op};
    top->op_a_shift = 0;
    top->op_d_p = 0;

    {body}

    delete top;
    std::cout << "Success" << std::endl;
    exit(0);
}}'''.format(test=test,body=body,name=name,op=opcode&0x1ff)


def compile(name, opcode, tests):
    verilatorcpp = harness(name, opcode, tests)
    with open('build/sim_'+name+'.cpp', "w") as f:
        f.write(verilatorcpp)



def run_verilator_test(verilog_file_name, driver_name, top_module):
    (_, filename, _, _, _, _) = inspect.getouterframes(inspect.currentframe())[1]
    file_path = os.path.dirname(filename)
    build_dir = os.path.join(file_path, 'build')
    assert not subprocess.call('verilator -Wall -Wno-INCABSPATH -Wno-DECLFILENAME --cc {}.v --exe {}.cpp --top-module {}'.format(verilog_file_name, driver_name, top_module), cwd=build_dir, shell=True)
    assert not subprocess.call('make -C obj_dir -j -f V{0}.mk V{0}'.format(top_module), cwd=build_dir, shell=True)
    assert not subprocess.call('./obj_dir/V{}'.format(top_module), cwd=build_dir, shell=True)
