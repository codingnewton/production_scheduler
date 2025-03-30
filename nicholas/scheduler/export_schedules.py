import pandas as pd
from matplotlib.patches import Rectangle
import numpy as np
import matplotlib.pyplot as plt

def export_schedules(res, model, export_location=''):
    for i, sol in enumerate(res):
        def visualize_schedule(solution_index, solution):
            # Create figure and axis
            fig, ax = plt.subplots(figsize=(15, 8))
            
            # Convert times to minutes for plotting
            tasks = []
            for member_id, member_tasks in solution[1].items():
                member_name = model.get_by_id(model.members, member_id).name
                for task in member_tasks:
                    start_mins = sum(int(x) * y for x, y in zip(task['start'].split(':'), [60, 1]))
                    end_mins = sum(int(x) * y for x, y in zip(task['end'].split(':'), [60, 1]))
                    tasks.append({
                        'Member': member_name,
                        'Task': f"Task {task['task']}",
                        'Start': start_mins,
                        'Duration': end_mins - start_mins
                    })
            
            # Convert to DataFrame for easier plotting
            df = pd.DataFrame(tasks)
            
            # Sort members by name
            members = sorted(df['Member'].unique())
            
            # Plot tasks as rectangles
            colors = plt.cm.Set3(np.linspace(0, 1, len(df['Task'].unique())))
            for idx, task in df.iterrows():
                y_pos = members.index(task['Member'])
                rect = Rectangle((task['Start'], y_pos - 0.25), task['Duration'], 0.5, 
                                facecolor=colors[int(task['Task'].split()[1]) % len(colors)])
                ax.add_patch(rect)
                ax.text(task['Start'] + task['Duration']/2, y_pos, 
                        task['Task'], ha='center', va='center')
            
            # Customize the plot
            ax.set_ylim(-0.5, len(members) - 0.5)
            ax.set_xlim(df['Start'].min(), (df['Start'] + df['Duration']).max())
            # ax.set_xlim(0*60, 24*60)  # 8:00 to 18:00
            ax.set_yticks(range(len(members)))
            ax.set_yticklabels(members)
            
            # Add gridlines
            ax.grid(True, axis='x', alpha=0.3)
            
            # Format x-axis as time
            # xticks = np.arange(0*60, 24*60, 60)
            xticks = np.arange(df['Start'].min(),(df['Start'] + df['Duration']).max() , 60)
            ax.set_xticks(xticks)
            ax.set_xticklabels([f'{int(x/60):02d}:00' for x in xticks])
            
            plt.title(f'Schedule Solution {solution_index + 1}')
            plt.tight_layout()
            
            # Save the plot
            plt.savefig(export_location+f'\\schedule_solution_{solution_index + 1}.png')
            plt.close()
            print(f'Solution {solution_index + 1} saved to {export_location}')

        visualize_schedule(i, sol)