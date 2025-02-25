# UI Pages Implementation

This directory contains the UI page implementations for the e-ink display driver application.

## Progress Bar Implementation

The progress bar functionality has been standardized in the `BaseTestPage` class. This ensures consistent behavior across all test pages.

### Key Features

- **Thread-safe updates**: Uses PyQt's signal/slot mechanism to ensure thread safety
- **Real-time progress updates**: Shows current progress percentage and image being processed
- **Dual update mechanisms**:
  - Direct callback from test controller
  - State change observation as a backup
- **Jump prevention**: Prevents progress from decreasing during test execution
- **Visual feedback**: Shows the current image being processed in the progress text

### Usage in Subclasses

When creating a new test page that extends `BaseTestPage`, follow these steps to ensure proper progress bar functionality:

1. Create the progress bar in your UI setup:
   ```python
   self.progress = self.create_progress_bar()
   layout.addWidget(self.progress)
   ```

2. The progress bar will automatically update during test execution through the registered callbacks.

3. No additional code is needed to handle progress updates, as the base class takes care of it.

### Implementation Details

The progress bar implementation consists of several components:

1. **Progress Bar Creation**: `create_progress_bar()` method in `BaseTestPage` creates a standardized progress bar.

2. **Progress Update Signal**: `progress_updated` signal is used to safely update the UI from any thread.

3. **Direct Callback**: `update_progress_direct()` method is registered with the test controller to receive direct progress updates.

4. **State Observation**: `on_state_changed()` method provides a backup mechanism for progress updates through state changes.

5. **UI Update Slot**: `_update_progress_ui()` slot is connected to the signal and updates the progress bar in the UI thread.

### Testing

The progress bar functionality is tested in `src/tests/ui/test_progress_bar.py`, which verifies:

- Correct progress bar creation
- Direct progress updates
- State-based progress updates
- Callback registration
- Progress updates during test execution
- Jump prevention

## Removed Components

The `ProgressDialog` class previously defined in `src/ui/widgets/progress.py` has been removed in favor of the standardized progress bar implementation in `BaseTestPage`. This ensures a more consistent user experience and simplifies the codebase.
