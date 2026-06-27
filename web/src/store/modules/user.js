/**

 * @description 登录、获取用户信息、退出登录、清除accessToken逻辑，不建议修改
 */

import { getUserInfo, login, logout } from "@/api/user";
import {
  getAccessToken,
  removeAccessToken,
  setAccessToken,
} from "@/utils/accessToken";
import router, { resetRouter } from "@/router";
import { title, tokenName } from "@/config";
import { ElMessage } from "element-plus";

const state = () => ({
  accessToken: getAccessToken(),
  username: "",
  avatar: "",
  permissions: [],
  roleNames: [], //  Add roleNames state
  routesLoaded: false
});
const getters = {
  accessToken: (state) => state.accessToken,
  username: (state) => state.username,
  avatar: (state) => state.avatar,
  permissions: (state) => state.permissions,
  roleNames: (state) => state.roleNames, //  Add roleNames getter
  routesLoaded: (state) => state.routesLoaded
};
const mutations = {
  setAccessToken(state, accessToken) {
    state.accessToken = accessToken;
    setAccessToken(accessToken);
  },
  setUsername(state, username) {
    state.username = username;
  },
  setAvatar(state, avatar) {
    state.avatar = avatar;
  },
  setPermissions(state, permissions) {
    state.permissions = permissions;
  },
  setRoleNames(state, roleNames) { //  Add setRoleNames mutation
    state.roleNames = roleNames;
  },
  SET_ROUTES_LOADED(state, loaded) {
    state.routesLoaded = loaded
  }
};
const actions = {
  setPermissions({ commit }, permissions) {
    commit("setPermissions", permissions);
  },
  async login({ commit }, userInfo) {
    const { data } = await login(userInfo);
    const accessToken = data[tokenName];
    if (accessToken) {
      commit("setAccessToken", accessToken);
      const hour = new Date().getHours();
      const thisTime =
        hour < 8
          ? "早上好"
          : hour <= 11
          ? "上午好"
          : hour <= 13
          ? "中午好"
          : hour < 18
          ? "下午好"
          : "晚上好";
      ElMessage.success(`欢迎登录${title}，${thisTime}！`);
    } else {
      ElMessage.error(`登录接口异常，未正确返回${tokenName}...`);
    }
  },
  async getUserInfo({ commit, state }) {
    try {
      const { data } = await getUserInfo(state.accessToken);
      if (!data) {
        ElMessage.error("验证失败，请重新登录...");
        return false;
      }
      let { permissions, username, avatar, roleNames } = data; //  Destructure roleNames
      if (permissions && username && Array.isArray(permissions)) {
        commit("setPermissions", permissions);
        commit("setRoleNames", roleNames || []); //  Commit roleNames
        commit("setUsername", username);
        commit("setAvatar", avatar);
        return permissions;
      } else {
        ElMessage.error("用户信息接口异常");
        return false;
      }
    } catch (error) {
      console.error("获取用户信息失败:", error);
      ElMessage.error("获取用户信息失败，请重新登录");
      return false;
    }
  },
  async logout({ dispatch, commit }) {
    // 保存当前路径用于登录后重定向
    const currentPath = router.currentRoute.value.fullPath;
    await logout(state.accessToken);
    await dispatch("resetAccessToken");
    commit("SET_ROUTES_LOADED", false);
    await resetRouter();
    // 跳转到登录页并携带当前路径，而非 location.reload()
    router.push(`/login?redirect=${currentPath}`);
  },
  resetAccessToken({ commit }) {
    commit("setPermissions", []);
    commit("setAccessToken", "");
    removeAccessToken();
  },
};
export default { state, getters, mutations, actions };
