import pandas as pd
from matplotlib.patches import Rectangle
import numpy as np
import matplotlib.pyplot as plt

def export_schedules(res, model, export_location=''):
    for i, sol in enumerate(res):
        def visualize_schedule(solution_index, solution):
            # Prepare data for plotting
            tasks = []
            for member_id, member_tasks in solution[1].items():
                member_name = model.get_by_id(model.members, member_id).name
                for task in member_tasks:
                    task_obj = model.get_by_id(model.tasks, task['task'])
                    
                    # Convert start and end time to minutes
                    start_mins = sum(int(x) * y for x, y in zip(task['start'].split(':'), [60, 1]))
                    end_mins = sum(int(x) * y for x, y in zip(task['end'].split(':'), [60, 1]))
                    
                    tasks.append({
                        'Member': member_name,
                        'MemberID': member_id,
                        'Task': f"Task {task['task']}",
                        'Task Description': task_obj.description,
                        'Start': start_mins,
                        'Duration': end_mins - start_mins,
                        'End': end_mins,
                    })
            
            # Convert to DataFrame for easier plotting
            df = pd.DataFrame(tasks)
            
            # Sort members by name
            members = sorted(df['Member'].unique())
            
            # Create figure and axes
            fig, ax = plt.subplots(figsize=(15, 12))
            
            # Define color palette
            task_colors = plt.cm.Set3(np.linspace(0, 1, len(df['Task'].unique())))
            
            # Plot tasks as rectangles
            for idx, task in df.iterrows():
                x_pos = members.index(task['Member'])
                task_idx = task['Task'].split()[1]  # Get the task number
                rect = Rectangle((x_pos - 0.25, task['Start']), 0.5, task['Duration'],
                                 facecolor=task_colors[int(task_idx) % len(df['Task'].unique())],
                                 label=f"Task {task_idx} - {task['Task Description']}")
                ax.add_patch(rect)
                ax.text(x_pos, task['Start'] + task['Duration']/2,
                        f'Task\n{task_idx}', ha='center', va='center', rotation=0)
            
            # Customize the plot
            ax.set_xlim(-0.5, len(members) - 0.5)
            ax.set_ylim(top=df['Start'].min(), bottom=(df['Start'] + df['Duration']).max())
            ax.set_xticks(range(len(members)))
            ax.set_xticklabels(members)
            
            # Add gridlines
            ax.grid(True, axis='y', alpha=0.3)
            
            # Format y-axis as time
            yticks = np.arange(df['Start'].min()-15,(df['Start'] + df['Duration']).max()+30 , 15)
            ax.set_yticks(yticks)
            ax.set_yticklabels([f'{y//60:02d}:{y%60:02d}' for y in yticks])

            # Move y-axis ticks to the right side and adjust appearance
            ax.yaxis.set_label_position('right')
            ax.yaxis.tick_right()

            # Add legend
            handles, labels = [], []
            for patch in ax.patches:
                handles.append(patch)
                labels.append(patch.get_label())

            # Remove duplicates while preserving order
            unique_labels = list(dict.fromkeys(labels))
            unique_handles = [handles[labels.index(label)] for label in unique_labels]  # Get unique handles
            unique_pairs = list(zip(unique_labels, unique_handles))  # Create pairs of labels and handles
            
            # Sort by task number
            sorted_pairs = sorted(unique_pairs, 
                                key=lambda x: int(x[0].split()[1]))  # Sort by task number
            
            # Unzip the sorted pairs
            labels, handles = zip(*sorted_pairs)
            ax.legend(handles, labels, 
                     loc='upper center', 
                     bbox_to_anchor=(0.5, -0.05),
                     fancybox=True, 
                     shadow=True, 
                     ncol=4,
                     title='Tasks')
          
            plt.title(f'Schedule Solution {solution_index + 1}')
            plt.tight_layout()
            
            # Save the timetable plot
            plt.savefig(export_location+f'/schedule_solution_{solution_index + 1}.png')
            plt.close()
            
            # Export to csv
            df_export = df.copy()
            df_export = df_export.sort_values(['Member', 'Start'])

            # Convert minutes back to time
            df_export['Start'] = df_export['Start'].apply(lambda x: f'{x//60:02d}:{x%60:02d}')
            df_export['End'] = df_export['End'].apply(lambda x: f'{x//60:02d}:{x%60:02d}')
            
            csv_filename = f'{export_location}/schedule_solution_{solution_index + 1}.csv'
            df_export.to_csv(csv_filename, index=False)
            print(f'Solution {solution_index + 1} saved to {export_location}')

        visualize_schedule(i, sol)