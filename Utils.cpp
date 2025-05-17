//
// Created by 唐雁 on 2024/2/19.
//

#include "Utils.h"
#include <iostream>

using namespace std;

long long getSystemTime() {
    // 获取当前时间点
    auto now = std::chrono::system_clock::now();
    // 转换为毫秒（Unix 时间戳）
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()
    );
    return ms.count();  // 返回毫秒数
}