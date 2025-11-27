import { store } from 'quasar/wrappers';
import { createPinia } from 'pinia';
import { createPersistedState } from 'pinia-plugin-persistedstate';

/*
 * When adding new properties to stores, you should also
 * extend the `PiniaCustomProperties` interface.
 * @see https://pinia.vuejs.org/core-concepts/plugins.html#typing-new-store-properties
 */
declare module 'pinia' {
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type
  export interface PiniaCustomProperties {
    // type the router added by the plugin above (#adding-new-external-properties)
    // router: Router
  }
}

/*
 * If not building with SSR mode, you can
 * directly export the Store instantiation;
 *
 * The function below can be async too; either use
 * async/await or return a Promise which resolves
 * with the Store instance.
 */

export default store((/* { ssrContext } */) => {
  const pinia = createPinia();

  // 添加持久化插件
  pinia.use(
    createPersistedState({
      storage: localStorage, // 使用localStorage持久化
      auto: true, // 自动持久化所有store
    }),
  );

  return pinia;
});
