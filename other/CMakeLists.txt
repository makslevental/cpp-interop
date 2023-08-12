add_library(other Main.cpp)

install(TARGETS other DESTINATION lib)
set_target_properties(other PROPERTIES PUBLIC_HEADER Main.h)
install(TARGETS other
        PUBLIC_HEADER
        DESTINATION include
        )