const API_BASE_URL = 'http://localhost:8000/api';

class TodoApp {
    constructor() {
        this.currentBoardId = null;
        this.currentProjectId = null;
        this.contextMenuTarget = null;

        // Initialize UI elements
        this.initializeElements();
        this.attachEventListeners();
        this.loadBoards();
    }

    initializeElements() {
        this.sidebarContent = document.getElementById('sidebarContent');
        this.newBoardBtn = document.getElementById('newBoardBtn');
        this.contextMenu = document.getElementById('contextMenu');
        this.newTaskInput = document.getElementById('newTaskInput');
        this.addTaskBtn = document.getElementById('addTaskBtn');
        this.tasksList = document.getElementById('tasksList');
        this.currentContext = document.getElementById('currentContext');
    }

    attachEventListeners() {
        // New board button
        this.newBoardBtn.addEventListener('click', () => this.createNewBoard());

        // Context menu
        document.addEventListener('click', () => this.hideContextMenu());
        document.getElementById('newProjectOption').addEventListener('click', () => this.createNewProject());
        document.getElementById('deleteOption').addEventListener('click', () => this.deleteItem());

        // Task creation
        this.addTaskBtn.addEventListener('click', () => this.createNewTask());
        this.newTaskInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.createNewTask();
        });
    }

    async loadBoards() {
        try {
            const response = await fetch(`${API_BASE_URL}/boards/`);
            const boards = await response.json();
            this.renderBoards(boards);
        } catch (error) {
            console.error('Error loading boards:', error);
        }
    }

    async createNewBoard() {
        const boardName = prompt('Enter board name:');
        if (!boardName) return;

        try {
            const response = await fetch(`${API_BASE_URL}/boards/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: boardName, settings: {} })
            });
            const newBoard = await response.json();
            this.loadBoards(); // Reload all boards
        } catch (error) {
            console.error('Error creating board:', error);
        }
    }

    async createNewProject() {
        if (!this.contextMenuTarget || !this.currentBoardId) return;

        const projectName = prompt('Enter project name:');
        if (!projectName) return;

        try {
            const response = await fetch(`${API_BASE_URL}/projects/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: projectName,
                    board_id: this.currentBoardId,
                    settings: {}
                })
            });
            const newProject = await response.json();
            this.loadBoards(); // Reload to show new project
        } catch (error) {
            console.error('Error creating project:', error);
        }
    }

    async createNewTask() {
        if (!this.currentProjectId || !this.newTaskInput.value.trim()) return;

        try {
            const response = await fetch(`${API_BASE_URL}/tasks/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_input: this.newTaskInput.value.trim(),
                    project_id: this.currentProjectId,
                    owner_ids: [],
                    tag_ids: []
                })
            });
            const newTask = await response.json();
            this.newTaskInput.value = '';
            this.loadTasks(this.currentProjectId);
        } catch (error) {
            console.error('Error creating task:', error);
        }
    }

    async loadTasks(projectId) {
        try {
            const response = await fetch(`${API_BASE_URL}/tasks/?project_id=${projectId}`);
            const tasks = await response.json();
            this.renderTasks(tasks);
        } catch (error) {
            console.error('Error loading tasks:', error);
        }
    }

    renderBoards(boards) {
        this.sidebarContent.innerHTML = '';
        boards.forEach(board => {
            const boardElement = this.createBoardElement(board);
            this.sidebarContent.appendChild(boardElement);
        });
    }

    createBoardElement(board) {
        const boardDiv = document.createElement('div');
        boardDiv.className = 'tree-item board-item';
        boardDiv.innerHTML = `
            <i class="fas fa-list"></i>
            <span>${board.name}</span>
        `;

        boardDiv.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.showContextMenu(e, board.id);
        });

        // Add projects if they exist
        if (board.projects && board.projects.length > 0) {
            const projectsContainer = document.createElement('div');
            projectsContainer.className = 'projects-container';
            board.projects.forEach(project => {
                const projectElement = this.createProjectElement(project);
                projectsContainer.appendChild(projectElement);
            });
            boardDiv.appendChild(projectsContainer);
        }

        return boardDiv;
    }

    createProjectElement(project) {
        const projectDiv = document.createElement('div');
        projectDiv.className = 'tree-item project-item';
        projectDiv.innerHTML = `
            <i class="fas fa-folder"></i>
            <span>${project.name}</span>
        `;

        projectDiv.addEventListener('click', () => {
            this.currentProjectId = project.id;
            this.currentContext.textContent = project.name;
            this.loadTasks(project.id);
        });

        return projectDiv;
    }

    renderTasks(tasks) {
        this.tasksList.innerHTML = '';
        tasks.forEach(task => {
            const taskElement = this.createTaskElement(task);
            this.tasksList.appendChild(taskElement);
        });
    }

    createTaskElement(task) {
        const taskDiv = document.createElement('div');
        taskDiv.className = 'task-item';
        taskDiv.innerHTML = `
            <span>${task.user_input}</span>
            <button class="delete-btn"><i class="fas fa-trash"></i></button>
        `;
        return taskDiv;
    }

    showContextMenu(e, boardId) {
        this.contextMenuTarget = e.target;
        this.currentBoardId = boardId;
        this.contextMenu.style.display = 'block';
        this.contextMenu.style.left = `${e.pageX}px`;
        this.contextMenu.style.top = `${e.pageY}px`;
    }

    hideContextMenu() {
        this.contextMenu.style.display = 'none';
        this.contextMenuTarget = null;
    }

    deleteItem() {
        // Implement deletion logic here
        this.hideContextMenu();
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    new TodoApp();
});