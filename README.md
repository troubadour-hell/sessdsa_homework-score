# sessdsa_homework-score
数据结构与算法课程作业提交评分系统

## 无限期停止维护

### **实现功能：**

* 学生：
  * 注册、登录
  * 提交作业
  * 查看成绩
  * 代码测试运行(借助brython实现)
  * 简单的OJ（限时功能工作得不太好，注释掉了）

  
* 助教：
  * 注册、登录
  * 下载、在线预览作业（py, pdf, 图片的预览）
  * 代码运行(借助brython实现)
  * 为作业评分
  * 查重（使用Stanford Moss系统）
  * 查看、导出成绩信息 
  
* 后台：
  * 发布作业
  * 更改助教状态
 
 
### 特性：

- 邮箱验证保障学生账号可靠性
- 作业上传后自动分配给助教评分
- 新的提交覆盖旧提交
- 只允许被标记为已选课的学生提交作业
- 可设置助教状态决定是否分配作业
- 作业单个、批量下载
- 评分时可提供反馈信息
- 所有助教批改进度显示
- python代码可在浏览器中运行

#### 登录页面
![登录页面](https://github.com/troubadour-hell/sessdsa_homework-score/blob/master/imgae/login.png?raw=true)

#### 学生主页
![学生主页](https://github.com/troubadour-hell/sessdsa_homework-score/blob/master/imgae/profile.png?raw=true)

#### 助教主页
![助教主页](https://github.com/troubadour-hell/sessdsa_homework-score/blob/master/imgae/ta_profile.png?raw=true)

#### 作业评分
![作业评分](https://github.com/troubadour-hell/sessdsa_homework-score/blob/master/imgae/score.png?raw=true)

#### 学生列表
![学生列表](https://github.com/troubadour-hell/sessdsa_homework-score/blob/master/imgae/students.png?raw=true)
