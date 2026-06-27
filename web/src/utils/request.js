// 解决跳转问题

import axios from "axios";
import {
  baseURL,
  contentType,
  debounce,
  invalidCode,
  loginInterception,
  noPermissionCode,
  requestTimeout,
  successCode,
  tokenName,
} from "@/config";
import store from "@/store";
import qs from "qs";
import router from "@/router";
import { isArray } from "@/utils/validate";
import { ElLoading, ElMessage } from "element-plus";
import { pickBy, identity } from "lodash-es";

let loadingInstance;

/**

 * @description 处理code异常
 * @param {*} code
 * @param {*} msg
 */
const handleCode = (code, msg) => {
  switch (code) {
    case invalidCode:
      ElMessage.error(msg || `后端接口${code}异常`);
      store.dispatch("user/resetAccessToken");
      if (loginInterception) {
        location.reload();
      }
      break;
    case noPermissionCode:
      router.push({ path: "/401" }).catch(() => { });
      break;
    default:
      ElMessage.error(msg || `后端接口${code}异常`);
      break;
  }
};

// 请求重试配置
const retryConfig = {
  retry: 0, // 重试次数
  retryDelay: 1000, // 重试间隔时间
};

// 创建axios实例
const instance = axios.create({
  baseURL,
  timeout: requestTimeout,
  headers: {
    "Content-Type": contentType,
  },
});

// 请求重试方法
instance.defaults.retry = retryConfig.retry;
instance.defaults.retryDelay = retryConfig.retryDelay;

// 请求拦截器
instance.interceptors.request.use(
  (config) => {
    const token = store.getters['user/accessToken']
    if (token) {
      config.headers['Authorization'] = 'Bearer ' + token
    }

    //这里会过滤所有为空、0、false的key，如果不需要请自行注释
    // if (config.data) config.data = pickBy(config.data, identity);
    if (
      config.data &&
      config.headers["Content-Type"] ===
      "application/x-www-form-urlencoded;charset=UTF-8"
    )
      config.data = qs.stringify(config.data);
    if (debounce.some((item) => config.url.includes(item)))
      loadingInstance = ElLoading.service();

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
instance.interceptors.response.use(
  (response) => {
    if (loadingInstance) loadingInstance.close();

    const { data, config } = response;

    // 🔥 新增：如果是下载文件（blob），直接返回 data，不进行 code 校验
    if (config.responseType === 'blob' || config.responseType === 'arraybuffer') {
      return data;
    }

    // 判断data是否为undefined或null
    if (data === undefined || data === null) {
      ElMessage.error("后端接口返回数据为空");
      return Promise.reject("后端接口返回数据为空");
    }

    // 获取 HTTP 状态码
    const httpStatus = response.status;

    // 安全地解构code和msg，避免undefined异常
    const code = data.code !== undefined ? data.code : null;
    const msg = data.msg !== undefined ? data.msg : "未知错误";

    // 操作正常Code数组
    const codeVerificationArray = isArray(successCode)
      ? [...successCode]
      : [...[successCode]];

    // 🔥 新增：兼容 DRF 标准返回格式（没有 code 字段的情况）
    // 如果没有 code 字段，则根据 HTTP 状态码判断是否成功（200-299 都视为成功）
    if (code === null) {
      if (httpStatus >= 200 && httpStatus < 300) {
        // HTTP 2xx 都视为成功，直接返回数据
        return data;
      } else {
        // HTTP 非2xx，视为失败
        handleCode(httpStatus, data.detail || data.message || msg);
        return Promise.reject(
          `请求失败: ${JSON.stringify({ url: config.url, status: httpStatus })}` || "Error"
        );
      }
    }

    // 原有逻辑：有 code 字段，检查 code 值
    if (codeVerificationArray.includes(code)) {
      return data;
    } else {
      handleCode(code, msg);
      return Promise.reject(
        `vue-admin-better请求异常拦截:${JSON.stringify({
          url: config.url,
          code,
          msg,
        })}` || "Error"
      );
    }
  },
  (error) => {
    if (loadingInstance) loadingInstance.close();

    // 处理请求重试
    const { config } = error;
    if (config && config.retry) {
      // 设置当前重试次数
      config.__retryCount = config.__retryCount || 0;

      // 检查是否可以重试
      if (config.__retryCount < config.retry) {
        // 增加重试次数
        config.__retryCount += 1;

        // 创建新的Promise进行重试
        const backoff = new Promise((resolve) => {
          setTimeout(() => {
            console.log(
              `重试请求: ${config.url}, 尝试次数: ${config.__retryCount}`
            );
            resolve();
          }, config.retryDelay || 1000);
        });

        // 重新发起请求
        return backoff.then(() => instance(config));
      }
    }

    // 处理undefined或无法解析的错误情况
    if (!error) {
      ElMessage.error("发生未知错误");
      return Promise.reject("发生未知错误");
    }

    const { response, message } = error;
    if (response && response.data) {
      const { data } = response;
      // 后端返回了标准的 {code, msg} 格式，直接显示 msg
      const errorMsg = data.msg || data.detail || message || "未知错误";
      ElMessage.error(errorMsg);
      return Promise.reject(error);
    } else {
      let errorMsg = "后端接口未知异常";

      if (message) {
        if (message === "Network Error") {
          errorMsg = "后端接口连接异常";
        } else if (message.includes("timeout")) {
          errorMsg = "后端接口请求超时";
        } else if (message.includes("Request failed with status code")) {
          const code = message.substr(message.length - 3);
          errorMsg = `后端接口${code}异常`;
        }
      }

      ElMessage.error(errorMsg);
      return Promise.reject(error);
    }
  }
);

export default instance;
