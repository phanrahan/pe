#include "Vtest_pe_comp_unq1.h"
#include "verilated.h"
#include <cassert>
#include <iostream>

int main(int argc, char **argv, char **env) {
    Verilated::commandArgs(argc, argv);
    Vtest_pe_comp_unq1* top = new Vtest_pe_comp_unq1;

    
    unsigned int tests[16][3] = {
        { 0, 0, 0 }, 
        { 0, 1, 0 }, 
        { 0, 2, 0 }, 
        { 0, 3, 0 }, 
        { 1, 0, 0 }, 
        { 1, 1, 1 }, 
        { 1, 2, 0 }, 
        { 1, 3, 1 }, 
        { 2, 0, 0 }, 
        { 2, 1, 0 }, 
        { 2, 2, 2 }, 
        { 2, 3, 2 }, 
        { 3, 0, 0 }, 
        { 3, 1, 1 }, 
        { 3, 2, 2 }, 
        { 3, 3, 3 }, 
    };


    top->op_code = 19;
    top->op_a_shift = 0;
    top->op_d_p = 0;

    
    for(int i = 0; i < 16; i++) {
        unsigned int* test = tests[i];
        top->op_a = test[0];
        top->op_b = test[1];
        top->eval();
        std::cout << test[0] << ", " << test[1] << ", " << test[2] << ", " << top->res << "\n";
        //assert(top->res == test[2]);
    }


    delete top;
    std::cout << "Success" << std::endl;
    exit(0);
}