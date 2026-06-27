// src/config/permission.js 解决跳转问题
import router from "@/router";
import store from "@/store";
import VabProgress from "nprogress";
import "nprogress/nprogress.css";
import getPageTitle from "@/utils/pageTitle";
import { getRouterList } from '@/api/router'  // 确保你有这个接口！
import {
  authentication,
  loginInterception,
  progressBar,
  recordRoute,
  routesWhiteList,
} from "@/config";
import { ElMessage } from "element-plus";

VabProgress.configure({
  easing: "ease",
  speed: 500,
  trickleSpeed: 200,
  showSpinner: false,
});

router.beforeEach(async (to, from, next) => {
  if (progressBar) VabProgress.start();

  let hasToken = store.getters["user/accessToken"];
  if (!loginInterception) hasToken = true;

  if (hasToken) {
    if (to.path === "/login") {
      next({ path: "/" });
      if (progressBar) VabProgress.done();
      return;
    }

    // 关键修复：判断是否已经加载过路由
    const hasRoutes = store.getters["user/routesLoaded"]

    if (hasRoutes) {
      next(); // 已加载，直接放行
      return;
    }

    try {
      let permissions = [];

      if (loginInterception) {
        // 正常登录：获取用户信息
        permissions = await store.dispatch("user/getUserInfo");
        if (!permissions) throw new Error("获取用户权限失败");
      } else {
        // 不拦截登录：给虚拟权限
        await store.dispatch("user/setPermissions", ["admin"]);
        permissions = ["admin"];
      }

      let accessRoutes = [];

      if (authentication === "all") {
        // all 模式：必须调用后端接口获取路由！
        const { data } = await getRouterList()
        if (!data || data.length === 0) {
          ElMessage.warning("当前用户没有任何菜单权限")
          next("/login")
          return
        }
        accessRoutes = await store.dispatch("routes/setAllRoutes", data)
      } else {
        accessRoutes = await store.dispatch("routes/setRoutes", permissions);
      }

      // 确保是数组
      if (!Array.isArray(accessRoutes)) {
        console.error("路由数据格式错误:", accessRoutes);
        accessRoutes = [];
      }

      // 添加路由
      accessRoutes.forEach(route => router.addRoute(route));

      // 关键！标记路由已加载，防止重复请求
      store.commit("user/SET_ROUTES_LOADED", true);

      // 修复重定向
      next({ ...to, replace: true });

    } catch (error) {
      console.error("路由守卫错误:", error);
      ElMessage.error("登录状态失效，请重新登录");
      await store.dispatch("user/resetAccessToken");
      next(`/login?redirect=${to.fullPath}`);
    } finally {
      if (progressBar) VabProgress.done();
    }
  } else {
    if (routesWhiteList.includes(to.path)) {
      next();
    } else {
      next(`/login?redirect=${to.fullPath}`);
      if (progressBar) VabProgress.done();
    }
  }

  // document.title = getPageTitle(to.meta.title);
});

router.afterEach((to, from) => {
  if (progressBar) VabProgress.done();
  document.title = getPageTitle(to.meta.title);
});
