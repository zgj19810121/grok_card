import yaml
import time
import random
import math


def load_task(source):
    if isinstance(source, dict):
        return source
    with open(source, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def apply_vars(obj, variables):
    """递归替换配置中的 {{变量名}}"""
    if not variables:
        return obj
    if isinstance(obj, str):
        for k, v in variables.items():
            obj = obj.replace("{{" + k + "}}", str(v))
        return obj
    if isinstance(obj, list):
        return [apply_vars(item, variables) for item in obj]
    if isinstance(obj, dict):
        return {k: apply_vars(v, variables) for k, v in obj.items()}
    return obj


def rand_delay(delay_cfg):
    """解析延迟配置，返回秒数。支持固定值或 [min, max] 随机范围"""
    if delay_cfg is None:
        return 0
    if isinstance(delay_cfg, list):
        return random.uniform(delay_cfg[0], delay_cfg[1]) / 1000
    return delay_cfg / 1000


def human_mouse_move(page, to_x, to_y, from_pos=None, steps_cfg=None):
    """贝塞尔曲线模拟人类鼠标移动轨迹"""
    if from_pos:
        from_x, from_y = from_pos
    else:
        from_x = random.randint(100, 400)
        from_y = random.randint(100, 400)

    # 生成1-2个随机控制点，形成贝塞尔曲线
    cp1_x = from_x + (to_x - from_x) * random.uniform(0.2, 0.5) + random.randint(-50, 50)
    cp1_y = from_y + (to_y - from_y) * random.uniform(0.2, 0.5) + random.randint(-50, 50)
    cp2_x = from_x + (to_x - from_x) * random.uniform(0.5, 0.8) + random.randint(-30, 30)
    cp2_y = from_y + (to_y - from_y) * random.uniform(0.5, 0.8) + random.randint(-30, 30)

    num_steps = steps_cfg or random.randint(20, 40)
    for i in range(num_steps + 1):
        t = i / num_steps
        # 三阶贝塞尔曲线
        x = (1-t)**3 * from_x + 3*(1-t)**2*t * cp1_x + 3*(1-t)*t**2 * cp2_x + t**3 * to_x
        y = (1-t)**3 * from_y + 3*(1-t)**2*t * cp1_y + 3*(1-t)*t**2 * cp2_y + t**3 * to_y
        page.mouse.move(x, y)
        # 模拟人类速度：中间快，两端慢
        speed = 2 + 6 * math.sin(t * math.pi)
        time.sleep(random.uniform(0.005, 0.02) / max(speed / 5, 0.5))
    return (to_x, to_y)


def mouse_idle(page, pos):
    """步骤间鼠标小范围微动，模拟真人手持"""
    if not pos:
        return pos
    x, y = pos
    for _ in range(random.randint(1, 3)):
        nx = x + random.uniform(-5, 5)
        ny = y + random.uniform(-5, 5)
        page.mouse.move(nx, ny)
        time.sleep(random.uniform(0.05, 0.15))
    return (nx, ny)


def move_and_click(page, selector, timeout=30000, from_pos=None):
    """鼠标移动到元素位置后点击"""
    el = page.wait_for_selector(selector, timeout=timeout)
    box = el.bounding_box()
    if box:
        # 点击位置加随机偏移，不总是正中心
        tx = box["x"] + box["width"] * random.uniform(0.3, 0.7)
        ty = box["y"] + box["height"] * random.uniform(0.3, 0.7)
        pos = human_mouse_move(page, tx, ty, from_pos)
        time.sleep(random.uniform(0.05, 0.15))
        page.mouse.click(tx, ty)
        return pos
    else:
        page.click(selector, timeout=timeout)
        return from_pos


def get_target(page, step):
    frame_sel = step.get("frame")
    if frame_sel:
        return page.frame_locator(frame_sel), True
    return page, False


def run_steps(page, steps, log, global_cfg=None, mouse_pos=None):
    global_cfg = global_cfg or {}
    global_delay = global_cfg.get("step_delay")
    use_human_mouse = global_cfg.get("human_mouse", False)

    for i, step in enumerate(steps):
        action = step["action"]
        selector = step.get("selector")
        timeout = step.get("timeout", 30000)
        log.append(f"步骤 {i+1}: {action} {selector or ''}")

        # 步骤前延迟：优先用步骤级别的，否则用全局的
        before = step.get("delay_before") or global_delay
        if before:
            wait_sec = rand_delay(before)
            # 等待期间鼠标微动
            if use_human_mouse and mouse_pos:
                mouse_pos = mouse_idle(page, mouse_pos)
            time.sleep(wait_sec)

        if "wait_for" in step:
            page.wait_for_selector(step["wait_for"], timeout=timeout)

        target, is_frame = get_target(page, step)

        force = step.get("force", False)

        if action == "click":
            if is_frame:
                target.locator(selector).click(timeout=timeout, force=force)
            elif use_human_mouse and not force:
                mouse_pos = move_and_click(page, selector, timeout, mouse_pos)
            else:
                target.click(selector, timeout=timeout, force=force)

        elif action == "fill":
            if is_frame:
                target.locator(selector).fill(step["value"], timeout=timeout)
            else:
                if use_human_mouse:
                    mouse_pos = move_and_click(page, selector, timeout, mouse_pos)
                time.sleep(random.uniform(0.2, 0.5))
                target.fill(selector, step["value"], timeout=timeout)

        elif action == "type":
            delay = step.get("type_delay", 100)
            # 先点击输入框获取焦点
            if is_frame:
                target.locator(selector).click()
            elif use_human_mouse:
                mouse_pos = move_and_click(page, selector, timeout, mouse_pos)
            else:
                target.click(selector)
            time.sleep(random.uniform(0.2, 0.5))
            # 逐字输入
            if isinstance(delay, list):
                for ch in step["value"]:
                    page.keyboard.type(ch, delay=0)
                    time.sleep(random.uniform(delay[0], delay[1]) / 1000)
            else:
                page.keyboard.type(step["value"], delay=delay)

        elif action == "press":
            if is_frame:
                target.locator(selector).press(step["key"])
            else:
                target.press(selector, step["key"])

        elif action == "check":
            if is_frame:
                target.locator(selector).check(timeout=timeout)
            else:
                page.check(selector, timeout=timeout)

        elif action == "uncheck":
            if is_frame:
                target.locator(selector).uncheck(timeout=timeout)
            else:
                page.uncheck(selector, timeout=timeout)

        elif action == "select":
            if is_frame:
                target.locator(selector).select_option(step["value"], timeout=timeout)
            else:
                page.select_option(selector, step["value"], timeout=timeout)

        elif action == "hover":
            if is_frame:
                target.locator(selector).hover(timeout=timeout)
            elif use_human_mouse:
                el = page.wait_for_selector(selector, timeout=timeout)
                box = el.bounding_box()
                if box:
                    tx = box["x"] + box["width"]/2
                    ty = box["y"] + box["height"]/2
                    mouse_pos = human_mouse_move(page, tx, ty, mouse_pos)
                else:
                    page.hover(selector)
            else:
                page.hover(selector)

        elif action == "focus":
            if is_frame:
                target.locator(selector).focus()
            else:
                page.focus(selector)

        elif action == "scroll":
            page.evaluate(
                f"document.querySelector('{selector}').scrollIntoView()" if selector
                else "window.scrollBy(0, {0})".format(step.get("y", 500))
            )

        elif action == "mouse_move":
            mouse_pos = human_mouse_move(page, step["x"], step["y"], mouse_pos, step.get("steps"))

        elif action == "wait":
            page.wait_for_selector(selector, timeout=timeout)

        elif action == "sleep":
            duration = step["duration"]
            time.sleep(rand_delay(duration) if isinstance(duration, list) else duration / 1000)

        elif action == "screenshot":
            page.screenshot(path=step.get("path", "screenshot.png"))

        elif action == "click_pos":
            # 用 JS 表达式返回 {x, y} 坐标，然后用鼠标点击
            try:
                coords = page.evaluate(step["js"])
            except Exception:
                coords = None
            if coords and coords.get("x") is not None:
                x, y = coords["x"], coords["y"]
                if use_human_mouse:
                    mouse_pos = human_mouse_move(page, x, y, mouse_pos)
                    time.sleep(random.uniform(0.05, 0.15))
                page.mouse.click(x, y)
                mouse_pos = (x, y)
                log.append(f"  点击坐标: ({x}, {y})")

        elif action == "js":
            try:
                result = page.evaluate(step["script"])
                log.append(f"  JS结果: {result}")
            except Exception as e:
                log.append(f"  JS出错: {e}")

        elif action == "upload":
            page.set_input_files(selector, step["files"])

        elif action == "goto":
            page.goto(step["url"], timeout=timeout)

        elif action == "back":
            page.go_back()

        elif action == "forward":
            page.go_forward()

        elif action == "reload":
            page.reload()

        elif action == "wait_url":
            pattern = step["pattern"]
            if "*" not in pattern and "http" not in pattern:
                pattern = f"**{pattern}**"
            page.wait_for_url(pattern, timeout=timeout)

        elif action == "loop":
            for j in range(step["count"]):
                log.append(f"  循环 {j+1}/{step['count']}")
                mouse_pos = run_steps(page, step["steps"], log, global_cfg, mouse_pos)

        elif action == "retry_until":
            max_retries = step.get("max_retries", 3)
            retry_delay = step.get("retry_delay", [2000, 5000])
            js_condition = step.get("js_condition")
            passed = False
            for attempt in range(max_retries):
                log.append(f"  重试 {attempt+1}/{max_retries}")
                try:
                    if step.get("steps"):
                        mouse_pos = run_steps(page, step["steps"], log, global_cfg, mouse_pos)
                    time.sleep(rand_delay(retry_delay))
                    if js_condition:
                        result = page.evaluate(js_condition)
                    else:
                        result = page.query_selector(selector)
                except Exception as e:
                    err = str(e).lower()
                    if "navigation" in err or "destroyed" in err or "closed" in err:
                        log.append(f"  页面已跳转，视为通过")
                        passed = True
                        break
                    log.append(f"  异常: {e}")
                    continue
                if result:
                    log.append(f"  条件满足，继续执行")
                    passed = True
                    if step.get("on_success"):
                        mouse_pos = run_steps(page, step["on_success"], log, global_cfg, mouse_pos)
                    break
            if not passed:
                log.append(f"  {max_retries}次重试均未通过，退出")
                raise Exception(f"retry_until 失败: {selector} 未出现")

        elif action == "if_exists":
            if page.query_selector(selector):
                mouse_pos = run_steps(page, step["steps"], log, global_cfg, mouse_pos)
            else:
                log.append(f"  元素不存在，跳过")

        else:
            log.append(f"  未知操作: {action}")

        # 步骤后延迟
        after = step.get("delay_after")
        if after:
            time.sleep(rand_delay(after))

    return mouse_pos


def run_task(task_source, variables=None):
    task = load_task(task_source)
    # 合并变量：YAML 里的 vars + 外部传入的 variables
    all_vars = task.get("vars", {})
    if variables:
        all_vars.update(variables)
    if all_vars:
        task = apply_vars(task, all_vars)

    log = [f"任务: {task['name']}", f"目标: {task['url']}"]
    browser_cfg = task.get("browser", {})
    global_cfg = task.get("timing", {})

    engine = browser_cfg.get("engine", "patchright")  # patchright 或 camoufox

    if engine == "camoufox":
        from camoufox.sync_api import Camoufox
        camo = Camoufox(
            headless=browser_cfg.get("headless", False),
            disable_coop=True,
            i_know_what_im_doing=True,
            window=(1280, 800),
        )
        browser = camo.__enter__()
        page = browser.new_page()
        try:
            page.goto(task["url"], timeout=60000, wait_until="domcontentloaded")
            log.append("页面已加载")
            run_steps(page, task["steps"], log, global_cfg)
            log.append("所有步骤执行完成")
            return True, log
        except Exception as e:
            log.append(f"执行出错: {e}")
            try:
                page.screenshot(path="error.png")
            except:
                pass
            return False, log
        finally:
            camo.__exit__(None, None, None)
    else:
        from patchright.sync_api import sync_playwright
        with sync_playwright() as p:
            # 选择浏览器类型
            channel = browser_cfg.get("channel")  # chrome, msedge, 或不填用默认
            incognito = browser_cfg.get("incognito", False)
            user_data = browser_cfg.get("user_data_dir")

            launch_args = {
                "headless": browser_cfg.get("headless", False),
                "slow_mo": browser_cfg.get("slow_mo", 0),
            }
            if channel:
                launch_args["channel"] = channel

            if user_data:
                # 持久化模式：保留 cookie、登录状态、缓存
                context = p.chromium.launch_persistent_context(user_data, **launch_args)
                page = context.pages[0] if context.pages else context.new_page()
                browser = context
            else:
                browser = p.chromium.launch(**launch_args)
                if incognito:
                    context = browser.new_context()
                    page = context.new_page()
                else:
                    page = browser.new_page()
            try:
                page.goto(task["url"], timeout=60000, wait_until="domcontentloaded")
                log.append("页面已加载")
                run_steps(page, task["steps"], log, global_cfg)
                log.append("所有步骤执行完成")
                return True, log
            except Exception as e:
                log.append(f"执行出错: {e}")
                page.screenshot(path="error.png")
                return False, log
            finally:
                browser.close()
