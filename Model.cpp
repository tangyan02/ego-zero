#include "Model.h"


#ifdef _WIN32
std::wstring ConvertStringToWString(const std::string& str) {
    std::wstring_convert<std::codecvt_utf8_utf16<wchar_t>> converter;
    return converter.from_bytes(str);
}
#endif //_WIN32

Model::Model() : memoryInfo(Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault)) {
}

void Model::init(string modelPath, string coreType)  {
    // 初始化环境
    env = new Ort::Env(ORT_LOGGING_LEVEL_WARNING, "ModelInference");

    // 初始化会话选项并添加模型
    sessionOptions = new Ort::SessionOptions();
    sessionOptions->SetIntraOpNumThreads(1);
    sessionOptions->SetGraphOptimizationLevel(ORT_ENABLE_ALL);

    // 判断是否有GPU
    auto providers = Ort::GetAvailableProviders();
    //看看有没有GPU支持列表
    //auto tensorRtAvailable = std::find(providers.begin(), providers.end(), "TensorrtExecutionProvider");
    //if ((tensorRtAvailable != providers.end()))//找到cuda列表
    //{
    //    std::cout << "found providers:" << std::endl;
    //    for (auto provider: providers)
    //        std::cout << provider << std::endl;
    //    std::cout << "use: TensorrtExecutionProvider" << std::endl;
    //    OrtTensorRTProviderOptions tensorRtProviderOptions;
    //    sessionOptions->AppendExecutionProvider_TensorRT(tensorRtProviderOptions);
    //}

    if (coreType == "gpu") {

        auto cudaAvailable = std::find(providers.begin(), providers.end(), "CUDAExecutionProvider");
        if ((cudaAvailable != providers.end())) //找到cuda列表
        {
//            memoryInfo = new Ort::MemoryInfo("Cuda", OrtAllocatorType::OrtArenaAllocator, 0, OrtMemTypeDefault);
            //memoryInfo = &Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);

            //std::cout << "found providers:" << std::endl;
            //for (auto provider : providers)
                //std::cout << provider << std::endl;
            //std::cout << "use: CUDAExecutionProvider" << std::endl;

            // CUDA 执行提供器配置
            OrtCUDAProviderOptions cuda_options;
            cuda_options.device_id = 0;
            cuda_options.arena_extend_strategy = 1;               // kSameAsRequested
            cuda_options.cudnn_conv_algo_search = OrtCudnnConvAlgoSearchHeuristic;
            cuda_options.do_copy_in_default_stream = false;       // 保持异步拷贝
            cuda_options.gpu_mem_limit = 0;                       // 自动管理显存
            cuda_options.has_user_compute_stream = 0;

            sessionOptions->AppendExecutionProvider_CUDA(cuda_options);

            // 会话优化配置
            sessionOptions->SetIntraOpNumThreads(1);
            sessionOptions->SetGraphOptimizationLevel(ORT_ENABLE_ALL);
            sessionOptions->DisableMemPattern();                  // 禁用内存模式
            sessionOptions->AddConfigEntry("disable_cpu_mem_buffer", "1");

            sessionOptions->AddConfigEntry("optimization.enable_mixed_precision", "1");

        }
        //cout << "cuda init finish" << endl;
    }


#ifdef _WIN32
    // 创建会话
    session = new Ort::Session(*env, ConvertStringToWString(modelPath).c_str(), *sessionOptions);
#endif //_WIN32

#if !defined(_WIN32) && (defined(__unix__) || defined(__unix) || (defined(__APPLE__) && defined(__MACH__)))
    session = new Ort::Session(*env, modelPath.c_str(), *sessionOptions);
#endif // __unix__
}

std::pair<float, std::vector<float> > Model::evaluate_state(vector<vector<vector<float> > > &data) {
    // 获取数据的维度
    int dim1 = data.size();
    int dim2 = data[0].size();
    int dim3 = data[0][0].size();

    // 将数据转换为一维数组
    std::vector<float> flattened_data(dim1 * dim2 * dim3);
    int index = 0;
    for (int i = 0; i < dim1; i++) {
        for (int j = 0; j < dim2; j++) {
            for (int k = 0; k < dim3; k++) {
                flattened_data[index++] = data[i][j][k];
            }
        }
    }

    std::vector<int64_t> input_tensor_shape = {dim1, dim2, dim3};
    Ort::Value input_tensor = Ort::Value::CreateTensor<float>(memoryInfo, flattened_data.data(),
                                                              flattened_data.size(), input_tensor_shape.data(),
                                                              input_tensor_shape.size());

    // 设置输入
    std::vector<const char *> input_node_names = {"input"};
    std::vector<Ort::Value> input_tensors;
    input_tensors.push_back(std::move(input_tensor));

    // 设置输出
    std::vector<const char *> output_node_names = {"value", "act"};

    // 进行推理
    auto output_tensors = session->Run(Ort::RunOptions{nullptr}, input_node_names.data(), input_tensors.data(),
                                       input_tensors.size(), output_node_names.data(), output_node_names.size());

    // 获取输出张量
    float value = *output_tensors[0].GetTensorMutableData<float>();

    float *output2 = output_tensors[1].GetTensorMutableData<float>();
    std::vector<int64_t> output2_shape = output_tensors[1].GetTensorTypeAndShapeInfo().GetShape();
    int output2_size = std::accumulate(output2_shape.begin(), output2_shape.end(), 1, std::multiplies<int64_t>());

    vector<float> prior_prob;
    for (int i = 0; i < output2_size; i++) {
        prior_prob.emplace_back(exp(output2[i]));
    }

    return std::make_pair(value, prior_prob);
}

vector<vector<vector<float> > > Model::get_state(Game &game) {
    int limit = 8;
    vector result(limit * 2 + 1, vector(game.boardSize, vector(game.boardSize, 0.0f)));;

    int k = 0;
    for (int i = game.history.size() - 1; i >= 0; i--) {
        auto board = game.history[i];
        for (int x = 0; x < game.boardSize; x++) {
            for (int y = 0; y < game.boardSize; y++) {
                if (board.board[x][y] == game.currentPlayer) {
                    result[k][x][y] = 1;
                }
            }
        }
        k++;
    }

    k = limit;
    for (int i = game.history.size() - 1; i >= 0; i--) {
        auto board = game.history[i];
        for (int x = 0; x < game.boardSize; x++) {
            for (int y = 0; y < game.boardSize; y++) {
                if (board.board[x][y] == 3 - game.currentPlayer) {
                    result[k][x][y] = 1;
                }
            }
        }
        k++;
    }

    k = limit * 2;
    if (game.currentPlayer == 1) {
        for (int x = 0; x < game.boardSize; x++) {
            for (int y = 0; y < game.boardSize; y++) {
                result[k][x][y] = 1;
            }
        }
    }

    return result;
}
