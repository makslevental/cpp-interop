#include "InterpreterUtils.h"

#include "clang/AST/Mangle.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Interpreter/Interpreter.h"
#include "clang/Sema/Lookup.h"
#include "clang/Sema/TemplateDeduction.h"

#include "llvm/Support/TargetSelect.h"

#include <iostream>
#include <memory>
#include <sstream>
#include <vector>

using namespace clang;

llvm::ExitOnError ExitOnErr;
std::unique_ptr<clang::Interpreter> CreateInterpreter() {
    std::vector<const char *> ClangArgv = {"-Xclang", "-emit-llvm-only"};
    clang::IncrementalCompilerBuilder CB;
    CB.SetCompilerArgs(ClangArgv);
    std::unique_ptr<clang::CompilerInstance> CI;
    CI = ExitOnErr(CB.CreateCpp());
    std::unique_ptr<clang::Interpreter> Interp;
    Interp = ExitOnErr(clang::Interpreter::create(std::move(CI)));
    return Interp;
}

struct LLVMInitRAII {
    LLVMInitRAII() {
        llvm::InitializeNativeTarget();
        llvm::InitializeNativeTargetAsmPrinter();
    }
    ~LLVMInitRAII() { llvm::llvm_shutdown(); }
} LLVMInit;

auto Interp = CreateInterpreter().release();

static LookupResult LookupName(Sema &SemaRef, const char *Name) {
    ASTContext &C = SemaRef.getASTContext();
    DeclarationName DeclName = &C.Idents.get(Name);
    LookupResult R(SemaRef, DeclName, SourceLocation(), Sema::LookupOrdinaryName);
    SemaRef.LookupName(R, SemaRef.TUScope);
    assert(!R.empty());
    return R;
}

Decl_t Clang_LookupName(const char *Name, Decl_t Context /*=0*/) {
    auto decl = LookupName(Interp->getCompilerInstance()->getSema(), Name).getFoundDecl();
    return decl;
}

FnAddr_t Clang_GetFunctionAddress(Decl_t D) {
    auto *ND = static_cast<clang::NamedDecl *>(D);
    clang::ASTContext &C = ND->getASTContext();
    std::unique_ptr<MangleContext> MangleC(C.createMangleContext());
    std::string mangledName;
    llvm::raw_string_ostream RawStr(mangledName);
    MangleC->mangleName(ND, RawStr);
    auto Addr = Interp->getSymbolAddress(RawStr.str());
    if (!Addr) {
        std::cerr << "couldn't find address for: " << RawStr.str() << "\n";
        throw std::exception();
    }
    return Addr->getValue();
}

void *Clang_CreateObject(Decl_t RecordDecl, int x) {
    std::cerr << "RecordDecl: " << RecordDecl << ", x: " << x << "\n";

    clang::TypeDecl *TD = static_cast<clang::TypeDecl *>(RecordDecl);
    std::string Name = TD->getQualifiedNameAsString();
    const clang::Type *RDTy = TD->getTypeForDecl();
    clang::ASTContext &C = Interp->getCompilerInstance()->getASTContext();
    size_t size = C.getTypeSize(RDTy);
    void *loc = malloc(size);

    // Tell the interpreter to call the default ctor with this memory. Synthesize:
    // new (loc) ClassName;
    static unsigned counter = 0;
    std::stringstream ss;
    if (Name == "A" || Name == "B" || Name == "C")
        ss << "auto _v" << counter++ << " = "
           << "new ((void*)" << loc << ")" << Name << "();";
    else
        ss << "auto _v" << counter++ << " = "
           << "new ((void*)" << loc << ")" << Name << "(" << x << ");";

    llvm::Error R = Interp->ParseAndExecute(ss.str());
    if (!R) {
        std::cerr << "couldn't construct " << ss.str() << " because " << toString(std::move(R)) << "\n";
        return nullptr;
    }

    return loc;
}


void Clang_Parse(const char *Code) {
    llvm::cantFail(Interp->Parse(Code));
}

void Clang_ParseExecute(const char *Code) {
    auto PTU1 = &llvm::cantFail(Interp->Parse(Code));
    llvm::cantFail(Interp->Execute(*PTU1));
}

/// auto f = &B::callme<A, int, C*>;
Decl_t Clang_InstantiateTemplate(Decl_t Scope, const char *Name, const char *Args) {
    static unsigned counter = 0;
    std::stringstream ss;
    NamedDecl *ND = static_cast<NamedDecl *>(Scope);
    // Args is empty.
    // FIXME: Here we should call Sema::DeduceTemplateArguments (for fn addr) and
    // extend it such that if the substitution is unsuccessful to get out the list
    // of failed candidates, eg TemplateSpecCandidateSet.
    ss << "auto _t" << counter++ << " = &" << ND->getNameAsString() << "::"
       << Name;
    llvm::StringRef ArgList = Args;
    if (!ArgList.empty())
        ss << '<' << Args << '>';
    ss << ';';
    auto PTU1 = &llvm::cantFail(Interp->Parse(ss.str()));
    llvm::cantFail(Interp->Execute(*PTU1));

    //PTU1->TUPart->dump();

    VarDecl *VD = static_cast<VarDecl *>(*PTU1->TUPart->decls_begin());
    UnaryOperator *UO = llvm::cast<UnaryOperator>(VD->getInit());
    return llvm::cast<DeclRefExpr>(UO->getSubExpr())->getDecl();
}