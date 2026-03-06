# Contributing to Quantum QE Enterprise

First off, thank you for considering contributing to Quantum QE! We want to keep our codebase clean, professional, and stable as we scale. To do so, please follow the guidelines below.

## 1. How to Contribute

We follow the standard **GitHub Flow**:
1. **Always branch off from `main`** for any bug fix or new feature.
2. Commit your changes locally following semantic commit messages.
3. Push your branch to the repository.
4. **Open a Pull Request (PR)** against the `main` branch.
5. Wait for CI checks to pass and for team code review before merging.

### Branch Naming Conventions
Please use descriptive branch names based on the work being done:
* `feature/short-description` - For any new features or capabilities.
* `fix/short-description` - For bug fixes.
* `docs/short-description` - For documentation changes.
* `refactor/short-description` - For code structure changes that don't alter functionality.

## 2. Setting Up Your Local Environment

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd qe-agent-mvp
   ```
2. Set up the Python Backend:
   ```bash
   # Create a virtual environment
   python -m venv venv
   
   # Activate it (Windows)
   .\venv\Scripts\Activate.ps1
   # OR (Linux/Mac)
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   playwright install chromium --with-deps
   ```
3. Set up the Next.js Frontend:
   ```bash
   cd qe-agent-ui
   npm install
   ```

## 3. Pull Request Process
* **Never push directly to `main`.** All changes must come through a Pull Request.
* When opening a PR, you will be prompted with a template. **Please fill it out completely.**
* The CI/CD pipeline will automatically run linting and tests against your code. Your PR **cannot** be merged if the CI pipeline fails.
* At least one approval from a Code Owner is required before a merge can be completed.

## 4. Environments
* **`main`**: The single source of truth. Code here must always be deployable.
* **Staging**: If we need a pre-production testing arena, we will utilize temporary environment branches or tags off of `main`.

Thank you for contributing!
