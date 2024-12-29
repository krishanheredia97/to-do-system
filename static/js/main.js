const API_BASE_URL = 'http://127.0.0.1:8000/api';

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
        document.getElementById('renameOption').addEventListener('click', () => this.renameItem());

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
            
            // Also fetch projects for each board
            for (let board of boards) {
                const projectsResponse = await fetch(`${API_BASE_URL}/projects/?board_id=${board.id}`);
                board.projects = await projectsResponse.json();
            }
            
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
        
        // Create board header
        const boardHeader = document.createElement('div');
        boardHeader.className = 'board-header';
        boardHeader.innerHTML = `
            <i class="fas fa-chevron-right"></i>
            <i class="fas fa-list"></i>
            <span>${board.name}</span>
        `;
        
        // Add context menu to board header
        boardHeader.addEventListener('contextmenu', (e) => {
            this.showContextMenu(e, 'board', board);
        });
        
        boardDiv.appendChild(boardHeader);
    
        // Create projects container
        const projectsContainer = document.createElement('div');
        projectsContainer.className = 'projects-container';
        projectsContainer.style.display = 'none'; // Hidden by default
        
        // Toggle projects visibility
        boardHeader.addEventListener('click', () => {
            const chevron = boardHeader.querySelector('.fa-chevron-right');
            chevron.classList.toggle('fa-chevron-down');
            projectsContainer.style.display = projectsContainer.style.display === 'none' ? 'block' : 'none';
        });
        
        if (board.projects && board.projects.length > 0) {
            board.projects.forEach(project => {
                const projectElement = this.createProjectElement(project);
                projectsContainer.appendChild(projectElement);
            });
        }
        
        boardDiv.appendChild(projectsContainer);
        return boardDiv;
    }

    createProjectElement(project) {
        const projectDiv = document.createElement('div');
        projectDiv.className = 'tree-item project-item';
        projectDiv.innerHTML = `
            <i class="fas fa-folder"></i>
            <span>${project.name}</span>
        `;
    
        projectDiv.addEventListener('click', (e) => {
            e.stopPropagation();
            document.querySelectorAll('.tree-item').forEach(item => item.classList.remove('selected'));
            projectDiv.classList.add('selected');
            
            this.currentProjectId = project.id;
            this.currentContext.textContent = project.name;
            this.loadTasks(project.id);
        });
    
        projectDiv.addEventListener('contextmenu', (e) => {
            this.showContextMenu(e, 'project', project);
        });
    
        return projectDiv;
    }

    renderTasks(tasks) {
        this.tasksList.innerHTML = '';
        
        // Create containers for incomplete and complete tasks
        const incompleteContainer = document.createElement('div');
        incompleteContainer.className = 'tasks-section incomplete-tasks';
        
        const completeContainer = document.createElement('div');
        completeContainer.className = 'tasks-section complete-tasks';
        completeContainer.innerHTML = '<h3>Completed Tasks</h3>';
        
        // Sort tasks into appropriate containers
        tasks.forEach(task => {
            const taskElement = this.createTaskElement(task);
            if (task.is_completed) {
                completeContainer.appendChild(taskElement);
            } else {
                incompleteContainer.appendChild(taskElement);
            }
        });
        
        // Add containers to the task list
        this.tasksList.appendChild(incompleteContainer);
        this.tasksList.appendChild(completeContainer);
    }

    createTaskElement(task) {
        const taskDiv = document.createElement('div');
        taskDiv.className = `task-item ${task.is_completed ? 'completed' : ''}`;
        taskDiv.innerHTML = `
            <div class="task-checkbox">
                <div class="circle-checkbox ${task.is_completed ? 'checked' : ''}"></div>
            </div>
            <span class="task-text">${task.user_input}</span>
            <button class="delete-btn"><i class="fas fa-trash"></i></button>
        `;
    
        // Handle task completion
        const checkbox = taskDiv.querySelector('.circle-checkbox');
        checkbox.addEventListener('click', () => this.toggleTaskCompletion(task.id, !task.is_completed));
    
        // Handle task deletion
        const deleteBtn = taskDiv.querySelector('.delete-btn');
        deleteBtn.addEventListener('click', () => this.deleteTask(task.id));
    
        return taskDiv;
    }

    async toggleTaskCompletion(taskId, completed) {
        try {
            await fetch(`${API_BASE_URL}/tasks/${taskId}/complete`, {
                method: 'PUT'
            });
            this.loadTasks(this.currentProjectId);
        } catch (error) {
            console.error('Error updating task:', error);
        }
    }

    async deleteTask(taskId) {
        try {
            await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
                method: 'DELETE'
            });
            this.loadTasks(this.currentProjectId);
        } catch (error) {
            console.error('Error deleting task:', error);
        }
    }

    async renameItem() {
        if (!this.contextMenuTarget) return;
        
        const newName = prompt('Enter new name:');
        if (!newName) return;

        try {
            const endpoint = this.contextMenuType === 'board' 
                ? `${API_BASE_URL}/boards/${this.contextMenuTarget.id}`
                : `${API_BASE_URL}/projects/${this.contextMenuTarget.id}`;

            await fetch(endpoint, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newName })
            });

            this.loadBoards();
        } catch (error) {
            console.error('Error renaming item:', error);
        }
        this.hideContextMenu();
    }

    async deleteItem() {
        if (!this.contextMenuTarget) return;

        if (!confirm('Are you sure you want to delete this item?')) return;

        try {
            const endpoint = this.contextMenuType === 'board' 
                ? `${API_BASE_URL}/boards/${this.contextMenuTarget.id}`
                : `${API_BASE_URL}/projects/${this.contextMenuTarget.id}`;

            await fetch(endpoint, {
                method: 'DELETE'
            });

            this.loadBoards();
        } catch (error) {
            console.error('Error deleting item:', error);
        }
        this.hideContextMenu();
    }

    showContextMenu(e, type, item) {
        e.preventDefault();
        e.stopPropagation();
        
        this.contextMenuTarget = item;
        this.contextMenuType = type;
        this.currentBoardId = type === 'board' ? item.id : item.board_id;
        
        // Show/hide appropriate menu items
        const newProjectOption = document.getElementById('newProjectOption');
        newProjectOption.style.display = type === 'board' ? 'block' : 'none';
        
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